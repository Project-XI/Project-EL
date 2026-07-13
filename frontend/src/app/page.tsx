"use client";

import { useRef } from "react";
import styles from "./page.module.css";
import Grainient from "../components/Grainient";

export default function Home() {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -344, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 344, behavior: 'smooth' });
    }
  };

  const features = [
    {
      id: 1,
      title: "Identity Verification",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      content: (
        <div className={styles.cardContent}>
          <div className={styles.successIcon}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" stroke="currentColor" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12l3 3 5-6" />
            </svg>
          </div>
          <span>Verified</span>
        </div>
      )
    },
    {
      id: 2,
      title: "Submission Parsing",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      content: (
        <div className={styles.cardContentAlt}>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Code Extraction</span>
            <div className={styles.swapValue}>
              <span>100%</span>
              <span style={{ fontSize: '14px', color: '#8b5cf6' }}>AST</span>
            </div>
          </div>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Complexity</span>
            <div className={styles.swapValue}>
              <span>High</span>
              <span style={{ fontSize: '14px', color: '#10b981' }}>O(n)</span>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 3,
      title: "Cross-Questioning",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
      content: (
        <div className={styles.cardContentPill}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="3">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Generated
        </div>
      )
    },
    {
      id: 4,
      title: "Multi-Model Panel",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      ),
      content: (
        <div className={styles.cardContentPanel}>
          <div className={styles.panelCircle}>A</div>
          <div className={styles.panelCircle}>B</div>
          <div className={styles.panelCircle}>C</div>
        </div>
      )
    },
    {
      id: 5,
      title: "Immutable Transcript",
      icon: (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      content: (
        <div className={styles.cardContentTranscript}>
          <span className={styles.lockIcon}>🔒</span>
          <span>Sealed</span>
        </div>
      )
    }
  ];

  return (
    <div className={styles.container}>
      <div className={styles.landingCard}>
        {/* Background Grainient */}
        <Grainient
          color1="#FF9FFC"
          color2="#5227FF"
          color3="#B497CF"
          timeSpeed={0.25}
          colorBalance={0}
          warpStrength={1}
          warpFrequency={5}
          warpSpeed={2}
          warpAmplitude={50}
          blendAngle={0}
          blendSoftness={0.05}
          rotationAmount={500}
          noiseScale={2}
          grainAmount={0.1}
          grainScale={2}
          grainAnimated={false}
          contrast={1.5}
          gamma={1}
          saturation={1}
          centerX={0}
          centerY={0}
          zoom={0.9}
        />

        {/* Navbar */}
        <nav className={styles.navbar}>
          <div className={styles.navLogoContainer}>
            <span className={styles.navLogoText} style={{ fontFamily: '"Cormorant Garamond", serif', fontSize: '1.4rem', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              TWELVE
            </span>
          </div>

          <div className={styles.navLinks}>
            <a href="#vision">Vision</a>
            <a href="#github">Github</a>
            <a href="#docs">Docs</a>
            <button className={styles.navButton}>Start Kiosk</button>
          </div>
        </nav>

        {/* Hero Section */}
        <main className={styles.hero}>
          <div className={styles.badge}>
            <span className={styles.badgeNew}>SYSTEM</span> AI-Powered Viva Assessment
          </div>

          <h1 className={styles.heroTitle}>
            Fairness Through AI.<br />No fear. No favour. Only knowledge.
          </h1>

          <div className={styles.heroButtons}>
            <a href="#" className={styles.buttonPrimary}>
              Start Examination
            </a>
            <a href="#" className={styles.buttonSecondary}>
              Admin Portal
            </a>
          </div>
        </main>

        {/* Bottom Right Toggle */}
        <div className={styles.demoToggleContainer}>
          <span className={styles.demoToggleLabel}>Kiosk Mode</span>
          <div className={styles.toggleSwitch}>
            <div className={styles.toggleKnob}></div>
          </div>
        </div>
      </div>

      {/* New Horizontal Scroll Section */}
      <section className={styles.featuresSection}>
        <div className={styles.featuresHeader}>
          <h2 className={styles.featuresTitle}>The complete assessment lifecycle</h2>
          <div className={styles.featuresNav}>
            <button className={styles.navArrow} onClick={scrollLeft}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button className={styles.navArrow} onClick={scrollRight}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <div className={styles.cardsContainer} ref={scrollContainerRef}>
          {features.map((feature) => (
            <div key={feature.id} className={styles.featureCard}>
              <div className={styles.cardInner}>
                {feature.content}
              </div>
              <div className={styles.cardLabel}>
                <div className={styles.cardIcon}>
                  {feature.icon}
                </div>
                {feature.title}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
