"use client";

interface Props {
  src: string;
  label: string;
}

export default function VideoPlayer({ src, label }: Props) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium text-zinc-400">{label}</p>
      <video
        key={src}
        controls
        playsInline
        autoPlay
        muted
        loop
        className="w-full rounded-xl bg-black"
        src={src}
        crossOrigin="anonymous"
      />
    </div>
  );
}
