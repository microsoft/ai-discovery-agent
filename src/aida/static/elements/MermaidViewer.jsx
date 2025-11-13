// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import { useEffect } from "react";

export default function MermaidViewer() {
  useEffect(() => {
    if (!window.mermaid) {
      const script = document.createElement("script");
      script.src =
        "https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.12.0/mermaid.min.js";
      script.async = true;
      script.integrity = "sha512-5TKaYvhenABhlGIKSxAWLFJBZCSQw7HTV7aL1dJcBokM/+3PNtfgJFlv8E6Us/B1VMlQ4u8sPzjudL9TEQ06ww==";
      script.crossOrigin = "anonymous";
      script.referrerPolicy = "no-referrer";
      document.body.appendChild(script);
      script.onload = () => {
        window.mermaid.initialize({
          securityLevel: "strict",
        });
        window.mermaid.contentLoaded();
      };
    } else {
      window.mermaid.initialize({
        securityLevel: "strict",
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
