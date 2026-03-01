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
        controls
        playsInline
        className="w-full rounded-xl bg-black"
        src={src}
      />
    </div>
  );
}
