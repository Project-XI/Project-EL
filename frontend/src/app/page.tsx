"use client";

import { useRef, useState, useEffect } from "react";
import styles from "./page.module.css";
import Grainient from "../components/Grainient";
import { TextReveal } from "../components/motion/text-reveal";
import { ExpandingArrowButton } from "../components/motion/expanding-arrow-button";

export default function Home() {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [qsCount, setQsCount] = useState(12);
  const [confidence, setConfidence] = useState(94.2);
  const [typewriterText, setTypewriterText] = useState("");

  useEffect(() => {
    const words = ["Analyzing AST...", "Finding Vulnerabilities...", "Generating Qs...", "Active ON"];
    let wordIdx = 0;
    let charIdx = 0;
    let isDeleting = false;
    let typingTimeout: NodeJS.Timeout;

    const type = () => {
      const currentWord = words[wordIdx];
      if (isDeleting) {
        charIdx--;
      } else {
        charIdx++;
      }

      setTypewriterText(currentWord.substring(0, charIdx) + "|");

      let delay = 60;
      if (!isDeleting && charIdx === currentWord.length) {
        delay = 1500;
        isDeleting = true;
      } else if (isDeleting && charIdx === 0) {
        isDeleting = false;
        wordIdx = (wordIdx + 1) % words.length;
        delay = 300;
      }

      typingTimeout = setTimeout(type, delay);
    };

    typingTimeout = setTimeout(type, 100);

    const numInterval = setInterval(() => {
      setQsCount(prev => prev < 45 ? prev + 1 : 12);
      setConfidence(prev => {
        const next = prev + (Math.random() * 0.8 - 0.2);
        return next > 99.9 ? 94.2 : next;
      });
    }, 400);

    return () => {
      clearTimeout(typingTimeout);
      clearInterval(numInterval);
    };
  }, []);

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
        <div className={styles.cardContentAlt}>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Viva Engine</span>
            <div className={styles.swapValue}>
              <span>{qsCount} Qs</span>
              <span style={{ fontSize: '14px', color: '#8b5cf6' }}>Ready</span>
            </div>
          </div>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Adversarial Mode</span>
            <div className={styles.swapValue}>
              <span style={{ minWidth: '160px', display: 'inline-block' }}>{typewriterText}</span>
              <span style={{ fontSize: '14px', color: '#10b981' }}></span>
            </div>
          </div>
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
        <div className={styles.cardContentAlt}>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Active Agents</span>
            <div className={styles.swapValue}>
              <span>3 Models</span>
              <span style={{ fontSize: '14px', color: '#3b82f6' }}>Sync</span>
            </div>
          </div>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Confidence Score</span>
            <div className={styles.swapValue}>
              <span style={{ minWidth: '60px', display: 'inline-block' }}>{confidence.toFixed(1)}%</span>
              <span style={{ fontSize: '14px', color: '#10b981' }}>High</span>
            </div>
          </div>
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
        <div className={styles.cardContentAlt}>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Session State</span>
            <div className={styles.swapValue}>
              <span>Sealed</span>
              <span style={{ fontSize: '14px', color: '#10b981' }}>Secured</span>
            </div>
          </div>
          <div className={styles.swapBox}>
            <span className={styles.swapLabel}>Audit Log</span>
            <div className={styles.swapValue}>
              <span>0x8F2...</span>
              <span style={{ fontSize: '14px', color: '#8b5cf6' }}>Tx ID</span>
            </div>
          </div>
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
            <a href="/docs">Docs</a>
            <button className={styles.navButton}>Start Kiosk</button>
          </div>
        </nav>

        {/* Hero Section */}
        <main className={styles.hero}>
          <div className={styles.badge}>
            <span className={styles.badgeNew}>SYSTEM</span> AI-Powered Viva Assessment
          </div>

          <TextReveal
            as="h1"
            className={styles.heroTitle}
            text={[
              "Fairness Through AI.",
              "No fear. No favour. Only",
              "knowledge."
            ]}
          />

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

      {/* Two Large Cards Section */}
      <section className={styles.largeCardsSection}>
        <div className={styles.largeCardsGrid}>

          {/* Card 1: The Viva Engine */}
          <div className={styles.largeCard}>
            <div className={styles.largeCardBg}>
              <Grainient color1="#FF9FFC" color2="#5227FF" color3="#B497CF" timeSpeed={0.25} colorBalance={0} warpStrength={1} warpFrequency={5} warpSpeed={2} warpAmplitude={50} blendAngle={0} blendSoftness={0.05} rotationAmount={500} noiseScale={2} grainAmount={0.1} grainScale={2} grainAnimated={false} contrast={1.5} gamma={1} saturation={1} centerX={0} centerY={0} zoom={3.5} />
            </div>
            <div className={styles.largeCardContent}>
              <div className={styles.largeCardLeft}>
                <div>
                  <h3 className={styles.largeCardTitle}>Submission<br />Intelligence</h3>
                  <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '1.1rem', maxWidth: '80%' }}>
                    The AI reconstructs your project into a semantic graph of concepts, dependencies, and implementation paths—creating a viva unique to your work.
                  </p>
                </div>
                <div className={styles.largeCardActions}>
                  <ExpandingArrowButton>View Demo</ExpandingArrowButton>
                </div>
              </div>
              <div className={styles.largeCardRight}>
                <div className={styles.mockUiPanel}>
                  <div className={styles.swapBox}>
                    <span className={styles.swapLabel}>Knowledge Graph</span>
                    <div className={styles.swapValue}>
                      <span>{130 + qsCount} Concepts</span>
                      <span style={{ fontSize: '14px', color: '#8b5cf6' }}>Generated</span>
                    </div>
                  </div>
                  <div className={styles.swapBox}>
                    <span className={styles.swapLabel}>Question Tree</span>
                    <div className={styles.swapValue}>
                      <span>Ready</span>
                      <span style={{ fontSize: '14px', color: '#10b981' }}>Dynamic</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Immutable Transcript */}
          <div className={styles.largeCard}>
            <div className={styles.largeCardBg}>
              <Grainient color1="#FF9FFC" color2="#5227FF" color3="#B497CF" timeSpeed={0.25} colorBalance={0} warpStrength={1} warpFrequency={5} warpSpeed={2} warpAmplitude={50} blendAngle={0} blendSoftness={0.05} rotationAmount={500} noiseScale={2} grainAmount={0.1} grainScale={2} grainAnimated={false} contrast={1.5} gamma={1} saturation={1} centerX={0} centerY={0} zoom={3.5} />
            </div>
            <div className={styles.largeCardContent}>
              <div className={styles.largeCardLeft}>
                <div>
                  <h3 className={styles.largeCardTitle}>Consensus<br />Evaluation</h3>
                  <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '1.1rem', maxWidth: '80%' }}>
                    Every answer is reviewed by multiple reasoning models before a unified score is produced. No assumptions. No examiner bias. Only evidence.
                  </p>
                </div>
                <div className={styles.largeCardActions}>
                  <ExpandingArrowButton>Explore Tx</ExpandingArrowButton>
                </div>
              </div>
              <div className={styles.largeCardRight}>
                <div className={styles.mockUiPanel}>
                  <div className={styles.swapBox}>
                    <span className={styles.swapLabel}>AI Panel</span>
                    <div className={styles.swapValue}>
                      <span>3 Models</span>
                      <span style={{ fontSize: '14px', color: '#3b82f6' }}>Online</span>
                    </div>
                  </div>
                  <div className={styles.swapBox}>
                    <span className={styles.swapLabel}>Confidence</span>
                    <div className={styles.swapValue}>
                      <span style={{ minWidth: '60px', display: 'inline-block' }}>{confidence.toFixed(1)}%</span>
                      <span style={{ fontSize: '14px', color: '#10b981' }}>Stable</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerLeft}>
            <span className={styles.footerLogo}>TWELVE</span>
            <p className={styles.footerDescription}>
              Fairness Through AI. No fear. No favour. Only knowledge.
            </p>
          </div>
          <div className={styles.footerRight}>
            <div className={styles.footerLinksGroup}>
              <h4>Product</h4>
              <a href="#">Features</a>
              <a href="#">Security</a>
              <a href="#">Pricing</a>
            </div>
            <div className={styles.footerLinksGroup}>
              <h4>Resources</h4>
              <a href="/docs" target="_blank" rel="noopener noreferrer">Documentation</a>
              <a href="#">API Reference</a>
              <a href="#">GitHub</a>
            </div>
            <div className={styles.footerLinksGroup}>
              <h4>Company</h4>
              <a href="#">About</a>
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
            </div>
          </div>
        </div>
        <div className={styles.footerBottom}>
          <p>© 2026 TWELVE. All rights reserved.</p>
          <div style={{ display: 'flex', gap: '24px' }}>
            <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Privacy Policy</a>
            <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
