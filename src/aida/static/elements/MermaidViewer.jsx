// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import { useEffect } from "react";

export default function MermaidViewer(props) {
  useEffect(() => {
    if (!window.mermaid) {
      const script = document.createElement("script");

      script.src =
        "https://cdnjs.cloudflare.com/ajax/libs/mermaid/9.3.0/mermaid.min.js";
      script.async = true;
      script.integrity = "sha512-ku2nmBrzAXY5YwohzTqLYH1/lvyMrpTVxgQKrvTabd/b/uesqltLORdmpVapYv6QhZVCLUX6wkvFaKOAY4xpUA==";
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
