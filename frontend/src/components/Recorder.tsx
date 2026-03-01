"use client";

import {
  useRef,
  useState,
  useEffect,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";

export interface RecorderHandle {
  getBlob: () => Blob | null;
  reset: () => void;
}

const MAX_SECONDS = 60;

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

interface RecorderProps {
  onClipChange?: (hasClip: boolean) => void;
}

const Recorder = forwardRef<RecorderHandle, RecorderProps>(function Recorder(
  { onClipChange },
  ref
) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "user",
            width: { ideal: 1280 },
            height: { ideal: 720 },
          },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setCameraReady(true);
      } catch {
        setCameraError(
          "Camera access denied. Please allow camera permissions and reload."
        );
      }
    }
    init();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const stopRecording = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    recorderRef.current?.stop();
    setRecording(false);
  }, []);

  const startRecording = useCallback(() => {
    if (!streamRef.current) return;
    if (typeof MediaRecorder === "undefined") {
      setCameraError("MediaRecorder is not supported in this browser.");
      return;
    }

    setBlob(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    chunksRef.current = [];
    setElapsed(0);

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(streamRef.current, {
        mimeType: "video/webm",
      });
    } catch {
      try {
        recorder = new MediaRecorder(streamRef.current);
      } catch {
        setCameraError("Could not create MediaRecorder.");
        return;
      }
    }

    recorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const b = new Blob(chunksRef.current, { type: "video/webm" });
      setBlob(b);
      const url = URL.createObjectURL(b);
      setPreviewUrl(url);
      onClipChange?.(true);
    };

    recorder.start();
    setRecording(true);

    let s = 0;
    timerRef.current = setInterval(() => {
      s += 1;
      setElapsed(s);
      if (s >= MAX_SECONDS) {
        if (timerRef.current) clearInterval(timerRef.current);
        recorder.stop();
        setRecording(false);
      }
    }, 1000);
  }, [previewUrl, onClipChange]);

  useImperativeHandle(ref, () => ({
    getBlob: () => blob,
    reset: () => {
      setBlob(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      setElapsed(0);
      onClipChange?.(false);
    },
  }));

  if (cameraError) {
    return (
      <div className="rounded-xl bg-red-900/20 border border-red-800/30 p-4 text-sm text-red-300">
        {cameraError}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative overflow-hidden rounded-xl bg-black">
        {!previewUrl ? (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full -scale-x-100"
            />
            {!cameraReady && (
              <div className="absolute inset-0 flex items-center justify-center text-sm text-zinc-500">
                Starting camera...
              </div>
            )}
            {recording && (
              <div className="absolute top-3 right-3 flex items-center gap-2 rounded-full bg-red-600/90 px-3 py-1.5 text-xs font-bold text-white shadow-lg">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-white" />
                {formatTime(elapsed)} / {formatTime(MAX_SECONDS)}
              </div>
            )}
          </>
        ) : (
          <video
            controls
            playsInline
            className="w-full"
            src={previewUrl}
          />
        )}
      </div>

      <div className="flex gap-3">
        {!recording && !previewUrl && (
          <button
            disabled={!cameraReady}
            onClick={startRecording}
            className="flex-1 rounded-xl bg-red-600 py-3.5 text-sm font-bold text-white transition-all hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Start Recording
          </button>
        )}
        {recording && (
          <button
            onClick={stopRecording}
            className="flex-1 rounded-xl bg-zinc-700 py-3.5 text-sm font-bold text-white transition-all hover:bg-zinc-600"
          >
            Stop Recording
          </button>
        )}
        {previewUrl && (
          <button
            onClick={() => {
              setBlob(null);
              if (previewUrl) URL.revokeObjectURL(previewUrl);
              setPreviewUrl(null);
              setElapsed(0);
              onClipChange?.(false);
            }}
            className="rounded-xl border border-zinc-700 px-5 py-3.5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800"
          >
            Re-record
          </button>
        )}
      </div>

      <p className="text-center text-xs text-zinc-600">
        Max {MAX_SECONDS}s &middot; No audio captured
      </p>
    </div>
  );
});

export default Recorder;
