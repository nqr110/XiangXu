// AppAudioCapture: per-process loopback (no muting). Requires Windows 10 20H2+ (build 19042+).
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Threading;

namespace AppAudioCapture
{
    internal static class Program
    {
        private const int ExitUsage = 1;
        private const int ExitUnsupported = 2;
        private const int ExitNoProcess = 3;
        private const int ExitRuntime = 4;

        public static int Main(string[] args)
        {
            string? mode = null;
            List<uint>? pids = null;
            int durationSec = -1;

            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--mode" && i + 1 < args.Length)
                {
                    mode = args[++i].ToLowerInvariant();
                    continue;
                }
                if (args[i] == "--pids" && i + 1 < args.Length)
                {
                    pids = new List<uint>();
                    foreach (string s in args[++i].Split(','))
                        if (uint.TryParse(s.Trim(), out uint pid))
                            pids.Add(pid);
                    continue;
                }
                if (args[i] == "--duration" && i + 1 < args.Length && int.TryParse(args[++i], out int d))
                {
                    durationSec = d;
                    continue;
                }
            }

            if (string.IsNullOrEmpty(mode) || pids == null || pids.Count == 0)
            {
                Console.Error.WriteLine("Usage: AppAudioCapture --mode include|exclude --pids <pid>[,pid...] [--duration <sec>]");
                return ExitUsage;
            }

            try
            {
                return RunProcessLoopback(mode, pids, durationSec);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("Error: " + ex.Message);
                return ExitRuntime;
            }
        }

        private static int RunProcessLoopback(string mode, List<uint> pids, int durationSec)
        {
            int loopbackMode = mode == "exclude" ? 1u : 0u; // 0 = include, 1 = exclude
            uint pid = pids[0];

            int hr = ProcessLoopbackCapture.Run(pid, loopbackMode, durationSec, (byte[] chunk) =>
            {
                try
                {
                    Console.OpenStandardOutput().Write(chunk, 0, chunk.Length);
                }
                catch (IOException) { }
            });
            return hr;
        }
    }

    internal static class ProcessLoopbackCapture
    {
        private const int ProcessLoopbackInclude = 0;
        private const int ProcessLoopbackExclude = 1;
        private const int ActivationTypeProcessLoopback = 2;
        private const ushort VT_BLOB = 65;
        private const int OutRate = 16000;
        private const int OutChannels = 1;
        private const int BytesPerSample = 2;

        private static readonly Guid IID_IAudioClient = new Guid("1CB9AD4C-DBFA-4c32-B178-C2F568A703B2");

        [StructLayout(LayoutKind.Sequential)]
        private struct ProcessLoopbackParams
        {
            public uint TargetProcessId;
            public uint ProcessLoopbackMode;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct ActivationParams
        {
            public uint CbSize;
            public int ActivationType;
            public ProcessLoopbackParams ProcessLoopbackParams;
        }

        [DllImport("ole32.dll")]
        private static extern int CoInitializeEx(IntPtr pvReserved, int dwCoInit);

        [DllImport("ole32.dll")]
        private static extern void CoUninitialize();

        [DllImport("Mmdevapi.dll", ExactSpelling = true, CharSet = CharSet.Unicode)]
        private static extern int ActivateAudioInterfaceAsync(
            [MarshalAs(UnmanagedType.LPWStr)] string devicePath,
            ref Guid riid,
            IntPtr activationParams,
            IActivateAudioInterfaceCompletionHandler completionHandler,
            out IActivateAudioInterfaceAsyncOperation activationOperation);

        public static int Run(uint targetPid, uint loopbackMode, int durationSec, Action<byte[]> onChunk)
        {
            int hr = CoInitializeEx(IntPtr.Zero, 0); // COINIT_APARTMENTTHREADED = 0x2
            if (hr != 0 && hr != 1) return ExitUnsupported;
            try
            {
                return RunCore(targetPid, loopbackMode, durationSec, onChunk);
            }
            finally
            {
                CoUninitialize();
            }
        }

        private static int ExitUnsupported => 2;

        private static int RunCore(uint targetPid, uint loopbackMode, int durationSec, Action<byte[]> onChunk)
        {
            var ap = new ActivationParams
            {
                CbSize = (uint)Marshal.SizeOf<ActivationParams>(),
                ActivationType = ActivationTypeProcessLoopback,
                ProcessLoopbackParams = new ProcessLoopbackParams
                {
                    TargetProcessId = targetPid,
                    ProcessLoopbackMode = loopbackMode
                }
            };

            int size = Marshal.SizeOf<ActivationParams>();
            IntPtr blobPtr = Marshal.AllocHGlobal(size);
            try
            {
                Marshal.StructureToPtr(ap, blobPtr, false);
                IntPtr propvariant = BuildPropVariantBlob(blobPtr, (uint)size);
                try
                {
                    var completion = new CompletionHandler();
                    int activateHr = ActivateAudioInterfaceAsync(
                        "VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK",
                        ref IID_IAudioClient,
                        propvariant,
                        completion,
                        out IActivateAudioInterfaceAsyncOperation op);
                    if (activateHr != 0)
                        return ExitUnsupported;
                    completion.Wait();
                    if (completion.Hr != 0 || completion.AudioClient == null)
                        return completion.Hr == unchecked((int)0x80070057) ? ExitNoProcess : ExitUnsupported;
                    return CaptureLoop(completion.AudioClient, durationSec, onChunk);
                }
                finally
                {
                    FreePropVariantBlob(propvariant);
                }
            }
            finally
            {
                Marshal.FreeHGlobal(blobPtr);
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct PropVariantBlob
        {
            public ushort vt;
            public ushort wReserved1;
            public ushort wReserved2;
            public ushort wReserved3;
            public int cbSize;
            public IntPtr pBlobData;
        }

        private static IntPtr BuildPropVariantBlob(IntPtr blobData, uint cbSize)
        {
            IntPtr p = Marshal.AllocHGlobal(Marshal.SizeOf<PropVariantBlob>());
            var pv = new PropVariantBlob
            {
                vt = VT_BLOB,
                wReserved1 = 0,
                wReserved2 = 0,
                wReserved3 = 0,
                cbSize = (int)cbSize,
                pBlobData = blobData
            };
            Marshal.StructureToPtr(pv, p, false);
            return p;
        }

        private static void FreePropVariantBlob(IntPtr p)
        {
            if (p != IntPtr.Zero)
                Marshal.FreeHGlobal(p);
        }

        private static int CaptureLoop(object audioClientObj, int durationSec, Action<byte[]> onChunk)
        {
            try
            {
                dynamic client = audioClientObj;
                client.Initialize(0, 0, 0, 0, IntPtr.Zero, IntPtr.Zero);
            }
            catch
            {
                return ExitNoProcess;
            }

            uint mixFormatTag = 1; // WAVE_FORMAT_PCM
            int channels = 2;
            int bitsPerSample = 16;
            int blockAlign = channels * (bitsPerSample / 8);
            int samplesPerSec = 48000;
            int bytesPerSec = samplesPerSec * blockAlign;
            ushort extraSize = 0;

            IntPtr wfxPtr = Marshal.AllocHGlobal(18 + extraSize);
            try
            {
                Marshal.WriteInt16(wfxPtr, 0, (short)1);
                Marshal.WriteInt16(wfxPtr, 2, (short)channels);
                Marshal.WriteInt32(wfxPtr, 4, samplesPerSec);
                Marshal.WriteInt32(wfxPtr, 8, bytesPerSec);
                Marshal.WriteInt16(wfxPtr, 12, (short)blockAlign);
                Marshal.WriteInt16(wfxPtr, 14, (short)bitsPerSample);
                Marshal.WriteInt16(wfxPtr, 16, (short)extraSize);

                try
                {
                    dynamic client = audioClientObj;
                    client.Initialize(0, 0, 10000000, 0, wfxPtr, IntPtr.Zero);
                }
                catch
                {
                    return ExitNoProcess;
                }

                uint bufferFrames = client.GetBufferSize();
                Type captureClientType = typeof(IAudioCaptureClient);
                Guid iidCapture = captureClientType.GUID;
                object? captureObj = client.GetService(ref iidCapture);
                if (captureObj == null) return ExitRuntime;
                dynamic capture = captureObj;
                client.Start();

                var deadline = durationSec > 0 ? DateTime.UtcNow.AddSeconds(durationSec) : (DateTime?)null;
                int frameSize = blockAlign;
                int chunkSamples = OutRate * 100 / 1000;
                int chunkBytesOut = chunkSamples * OutChannels * BytesPerSample;
                var outBuf = new byte[chunkBytesOut];
                var inBuf = new byte[4096];

                while (deadline == null || DateTime.UtcNow < deadline.Value)
                {
                    uint packetLength = capture.GetNextPacketSize();
                    if (packetLength == 0)
                    {
                        Thread.Sleep(5);
                        continue;
                    }
                    IntPtr dataPtr = capture.GetBuffer(out int numFrames, out int flags, out long _, out long _);
                    if (numFrames <= 0) continue;
                    int copyBytes = Math.Min(numFrames * frameSize, inBuf.Length);
                    Marshal.Copy(dataPtr, inBuf, 0, copyBytes);
                    capture.ReleaseBuffer(numFrames);
                    ResampleTo16kMono(inBuf, copyBytes, samplesPerSec, channels, outBuf);
                    onChunk(outBuf);
                }

                try { client.Stop(); } catch { }
                return 0;
            }
            finally
            {
                Marshal.FreeHGlobal(wfxPtr);
            }
        }

        private static void ResampleTo16kMono(byte[] raw, int length, int inRate, int inChannels, byte[] outBuf)
        {
            int inSamples = length / 2;
            if (inChannels == 2) inSamples /= 2;
            int outSamples = outBuf.Length / 2;
            double ratio = (double)inSamples / outSamples;
            for (int i = 0; i < outSamples; i++)
            {
                double src = i * ratio;
                int i0 = (int)src;
                int i1 = Math.Min(i0 + 1, inSamples - 1);
                if (i1 < 0) i1 = i0;
                float frac = (float)(src - i0);
                int idx0 = inChannels == 2 ? i0 * 2 : i0;
                int idx1 = inChannels == 2 ? i1 * 2 : i1;
                short s0 = BitConverter.ToInt16(raw, Math.Min(idx0 * 2, length - 2));
                short s1 = BitConverter.ToInt16(raw, Math.Min(idx1 * 2, length - 2));
                if (inChannels == 2 && idx0 * 2 + 2 < length)
                    s0 = (short)((s0 + BitConverter.ToInt16(raw, idx0 * 2 + 2)) / 2);
                if (inChannels == 2 && idx1 * 2 + 2 < length)
                    s1 = (short)((s1 + BitConverter.ToInt16(raw, idx1 * 2 + 2)) / 2);
                int v = (int)(s0 * (1 - frac) + s1 * frac);
                v = Math.Max(-32768, Math.Min(32767, v));
                BitConverter.GetBytes((short)v).CopyTo(outBuf, i * 2);
            }
        }

        private sealed class CompletionHandler : IActivateAudioInterfaceCompletionHandler
        {
            private readonly ManualResetEvent _done = new ManualResetEvent(false);
            public int Hr;
            public object? AudioClient;

            public void ActivateCompleted(IActivateAudioInterfaceCompletionParams activateParams)
            {
                try
                {
                    activateParams.GetActivateResult(out Hr, out object? result);
                    AudioClient = result;
                }
                catch { Hr = -1; }
                _done.Set();
            }

            public void Wait() => _done.WaitOne();
        }
    }

    [ComImport]
    [Guid("41D949AB-9862-444A-80F6-C261334DA255")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IActivateAudioInterfaceCompletionHandler
    {
        void ActivateCompleted(IActivateAudioInterfaceCompletionParams activateParams);
    }

    [ComImport]
    [Guid("72A22D78-CDE4-431D-B8CC-843A71199B6D")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IActivateAudioInterfaceCompletionParams
    {
        void GetActivateResult(out int activateResult, [MarshalAs(UnmanagedType.IUnknown)] out object? activatedInterface);
    }

    [ComImport]
    [Guid("B4FBF83F-7B82-4B2C-9B6B-9A0FEF0C6A60")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IActivateAudioInterfaceAsyncOperation
    {
        void GetActivateResult(out int activateResult, [MarshalAs(UnmanagedType.IUnknown)] out object? activatedInterface);
    }

    [ComImport]
    [Guid("C8ADBD64-E71E-48a0-A4DE-185C395CD317")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IAudioCaptureClient
    {
        int GetNextPacketSize();
        IntPtr GetBuffer(out int numFramesRequested, out int flags, out long devicePosition, out long qpcPosition);
        void ReleaseBuffer(int numFramesRead);
    }
}
