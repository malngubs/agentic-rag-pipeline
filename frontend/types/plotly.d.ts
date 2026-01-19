/**
 * Type declarations for plotly.js-dist-min
 */
declare module 'plotly.js-dist-min' {
  export interface Data {
    type?: string;
    x?: any[];
    y?: any[];
    z?: any[];
    values?: any[];
    labels?: string[];
    text?: string[] | string;
    name?: string;
    mode?: string;
    marker?: {
      color?: string | string[];
      size?: number | number[];
      line?: {
        color?: string;
        width?: number;
      };
    };
    line?: {
      color?: string;
      width?: number;
      shape?: string;
    };
    fill?: string;
    fillcolor?: string;
    hoverinfo?: string;
    textinfo?: string;
    hole?: number;
    [key: string]: any;
  }

  export interface Layout {
    title?: string | { text: string; font?: any };
    xaxis?: {
      title?: string | { text: string };
      type?: string;
      tickformat?: string;
      showgrid?: boolean;
      gridcolor?: string;
      linecolor?: string;
      tickfont?: any;
      [key: string]: any;
    };
    yaxis?: {
      title?: string | { text: string };
      type?: string;
      tickformat?: string;
      showgrid?: boolean;
      gridcolor?: string;
      linecolor?: string;
      tickfont?: any;
      [key: string]: any;
    };
    width?: number;
    height?: number;
    margin?: { l?: number; r?: number; t?: number; b?: number; pad?: number };
    paper_bgcolor?: string;
    plot_bgcolor?: string;
    font?: { color?: string; family?: string; size?: number };
    showlegend?: boolean;
    legend?: { x?: number; y?: number; orientation?: string; font?: any };
    autosize?: boolean;
    [key: string]: any;
  }

  export interface Config {
    responsive?: boolean;
    displayModeBar?: boolean;
    displaylogo?: boolean;
    modeBarButtonsToRemove?: string[];
    scrollZoom?: boolean;
    [key: string]: any;
  }

  export function newPlot(
    graphDiv: HTMLElement | string,
    data: Data[],
    layout?: Partial<Layout>,
    config?: Partial<Config>
  ): Promise<any>;

  export function react(
    graphDiv: HTMLElement | string,
    data: Data[],
    layout?: Partial<Layout>,
    config?: Partial<Config>
  ): Promise<any>;

  export function purge(graphDiv: HTMLElement | string): void;

  export function relayout(
    graphDiv: HTMLElement | string,
    update: Partial<Layout>
  ): Promise<any>;

  export function restyle(
    graphDiv: HTMLElement | string,
    update: Partial<Data>,
    traceIndices?: number | number[]
  ): Promise<any>;

  export function update(
    graphDiv: HTMLElement | string,
    dataUpdate: Partial<Data>,
    layoutUpdate: Partial<Layout>,
    traceIndices?: number | number[]
  ): Promise<any>;
}
