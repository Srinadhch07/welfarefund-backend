import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders Welfare Fund API Navigation', () => {
    render(<App />);
    expect(screen.getByText('Welfare Fund API Navigation')).toBeDefined();
  });
});
