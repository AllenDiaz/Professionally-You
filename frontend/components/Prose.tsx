import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders model/user text as markdown in the serif reading face. */
export function Prose({ content }: { content: string }) {
  return (
    <div className="space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: (props) => (
            <a
              {...props}
              target="_blank"
              rel="noreferrer noopener"
              className="text-phosphor underline underline-offset-2 hover:opacity-80"
            />
          ),
          code: (props) => (
            <code
              {...props}
              className="rounded bg-panel border border-rule px-1 py-0.5 font-mono text-[0.85em]"
            />
          ),
          ul: (props) => <ul {...props} className="list-disc pl-5 space-y-1" />,
          ol: (props) => <ol {...props} className="list-decimal pl-5 space-y-1" />,
          p: (props) => <p {...props} className="leading-relaxed" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
