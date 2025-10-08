import { useEffect } from "react";

export default function MyComponent() {
  useEffect(() => {
    if (!window.mermaid) {
      const script = document.createElement("script");
      script.src =
        "https://cdnjs.cloudflare.com/ajax/libs/mermaid/9.3.0/mermaid.min.js";
      script.async = true;
      document.body.appendChild(script);
      script.onload = () => {
        window.mermaid.initialize({
          securityLevel: "loose",
        });
        window.mermaid.contentLoaded();
      };
    } else {
      window.mermaid.initialize({
        securityLevel: "loose",
      });
      window.mermaid.contentLoaded();
    }
  }, []);

  return (
    <div>
      <div>Mermaid Diagram {props.id}</div>
      <div className="mermaid">{props.code || "No Mermaid code provided."}</div>
    </div>
  );
}
