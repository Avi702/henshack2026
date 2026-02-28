"use client";

interface Props {
  src: string;
  label: string;
}

export default function VideoPlayer({ src, label }: Props) {
  return (
    <div>
      <p className="mb-1.5 text-sm font-medium text-slate-400">{label}</p>
      <video
        controls
        playsInline
        className="w-full rounded-lg bg-black"
        src={src}
      />
    </div>
  );
}
