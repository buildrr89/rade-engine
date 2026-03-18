export default function Layout({ children }: { children: unknown }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
