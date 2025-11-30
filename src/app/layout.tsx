"use client";
import "globals.css";
import { TopNavBar } from "components/TopNavBar";
import { Analytics } from "@vercel/analytics/react";
import { Provider } from "react-redux";
import { store } from "lib/redux/store";
import Head from "next/head";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <Head>
        <title>AI Resume - Free Open-source Resume Builder and Parser</title>
        <meta
          name="description"
          content="AI Resume is a free, open-source, and powerful resume builder that allows anyone to create a modern professional resume in 3 simple steps. For those who have an existing resume, AI Resume also provides a resume parser to help test and confirm its ATS readability."
        />
      </Head>
      <body>
        <Provider store={store}>
          <TopNavBar />
          {children}
          <Analytics />
        </Provider>
      </body>
    </html>
  );
}
