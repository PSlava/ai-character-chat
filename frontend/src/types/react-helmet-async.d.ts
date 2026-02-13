declare module 'react-helmet-async' {
  import { Component, ReactNode } from 'react';

  interface HelmetProps {
    children?: ReactNode;
  }

  export class Helmet extends Component<HelmetProps> {}

  interface HelmetProviderProps {
    children?: ReactNode;
  }

  export class HelmetProvider extends Component<HelmetProviderProps> {}
}
