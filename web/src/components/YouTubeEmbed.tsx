/** A short instructional video (T-05), embedded as a facade: the page ships a thumbnail `<img
 * loading="lazy">` and a link, never the YouTube player itself, until a reader actually asks for
 * it by clicking. No autoplay, no third-party script loaded up front, and - since the facade is a
 * real `<a href="https://www.youtube.com/watch?v=...">` - a reader with no JavaScript still gets a
 * working link to the video rather than a dead button.
 *
 * TWO LINKS TO THE SAME VIDEO ON PURPOSE. The thumbnail carries the accessible name (`aria-label`,
 * "Play video: <title>"); the caption below it is the same link with the title as its own visible
 * text, which is also what lets a reader (and this site's own markdown sibling, `pageMarkdown`)
 * see which video this is without opening it. */
import { useState } from "react";

export function YouTubeEmbed({ videoId, title }: { videoId: string; title: string }) {
  const [playing, setPlaying] = useState(false);
  const watchUrl = `https://www.youtube.com/watch?v=${videoId}`;

  const play = (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setPlaying(true);
  };

  return (
    <div className="max-w-[40rem]">
      {playing ? (
        <div className="relative aspect-video w-full overflow-hidden border border-[var(--color-line)] bg-black">
          <iframe
            className="absolute inset-0 h-full w-full"
            src={`https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1`}
            title={title}
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
          />
        </div>
      ) : (
        <a
          href={watchUrl}
          onClick={play}
          aria-label={`Play video: ${title}`}
          className="relative block aspect-video w-full overflow-hidden border border-[var(--color-line)] bg-[var(--color-paper-2)]"
        >
          <img
            src={`https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`}
            alt=""
            loading="lazy"
            className="absolute inset-0 h-full w-full object-cover"
          />
          <span aria-hidden="true" className="absolute inset-0 flex items-center justify-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-black/70 text-lg text-white">
              &#9654;
            </span>
          </span>
        </a>
      )}
      <p className="mt-2 text-sm text-[var(--color-ink-2)]">
        <a href={watchUrl} onClick={play} className="hover:underline">
          {title}
        </a>
      </p>
    </div>
  );
}
