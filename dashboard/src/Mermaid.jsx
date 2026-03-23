import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#10b981',
    primaryTextColor: '#fafafa',
    primaryBorderColor: '#27272a',
    lineColor: '#3f3f46',
    secondaryColor: '#18181b',
    tertiaryColor: '#111113',
    background: '#111113',
    mainBkg: '#18181b',
    nodeBorder: '#3f3f46',
    clusterBkg: '#111113',
    clusterBorder: '#27272a',
    titleColor: '#fafafa',
    edgeLabelBackground: '#18181b',
    fontSize: '13px',
  },
  flowchart: { curve: 'basis', padding: 16 },
  securityLevel: 'loose',
});

let counter = 0;

export default function Mermaid({ chart, className = '' }) {
  const ref = useRef(null);
  const [svg, setSvg] = useState('');
  const id = useRef(`mermaid-${counter++}`);

  useEffect(() => {
    if (!chart) return;
    mermaid.render(id.current, chart).then(({ svg }) => {
      setSvg(svg);
    }).catch(() => {});
  }, [chart]);

  return (
    <div
      ref={ref}
      className={className}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
