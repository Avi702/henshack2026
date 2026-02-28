"use client";

import {
  useState,
  useRef,
  forwardRef,
  useImperativeHandle,
  useEffect,
} from "react";

const MAX_SIZE_MB = 50;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;
const MAX_DURATION = 60;

export interface UploaderHandle {
  getBlob: () => Blob | null;
  reset: () => void;
}

interface UploaderProps {
  onClipChange?: (hasClip: boolean) => void;
}

const Uploader = forwardRef<UploaderHandle, UploaderProps>(function Uploader(
  { onClipChange },
  ref
) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function handleFile(f: File) {
    setError(null);

    if (f.size > MAX_SIZE_BYTES) {
      setError(`File too large (${(f.size / 1024 / 1024).toFixed(1)} MB). Max is ${MAX_SIZE_MB} MB.`);
      return;
    }

    // Validate duration via hidden video element
    const url = URL.createObjectURL(f);
    const vid = document.createElement("video");
    vid.preload = "metadata";
    vid.onloadedmetadata = () => {
      if (vid.duration > MAX_DURATION) {
        setError(
          `Video is ${Math.round(vid.duration)}s long. Max allowed is ${MAX_DURATION}s.`
        );
        URL.revokeObjectURL(url);
        return;
      }
      setFile(f);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(url);
      onClipChange?.(true);
    };
    vid.onerror = () => {
      // Can't read metadata — accept file anyway (server will validate)
      setFile(f);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(url);
      onClipChange?.(true);
    };
    vid.src = url;
  }

  useImperativeHandle(ref, () => ({
    getBlob: () => file,
    reset: () => {
      setFile(null);
      setError(null);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
      if (inputRef.current) inputRef.current.value = "";
      onClipChange?.(false);
    },
  }));

  return (
    <div className="space-y-4">
      <label
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const f = e.dataTransfer.files?.[0];
          if (f) handleFile(f);
        }}
        className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-800/40 p-10 text-center transition-colors hover:border-blue-600/50 hover:bg-slate-800/60"
      >
        <svg
          className="mb-3 h-10 w-10 text-slate-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
        <p className="text-sm text-slate-400">
          Drag & drop or <span className="text-blue-400 underline">browse</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">
          MP4, MOV, or WebM &middot; Max {MAX_SIZE_MB} MB &middot; Max{" "}
          {MAX_DURATION}s
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/webm"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
      </label>

      {error && (
        <div className="rounded-lg bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {previewUrl && (
        <div className="space-y-3">
          <video
            controls
            playsInline
            className="w-full rounded-xl bg-black"
            src={previewUrl}
          />
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">{file?.name}</p>
            <button
              onClick={() => {
                setFile(null);
                if (previewUrl) URL.revokeObjectURL(previewUrl);
                setPreviewUrl(null);
                if (inputRef.current) inputRef.current.value = "";
                onClipChange?.(false);
              }}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Remove
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

export default Uploader;
