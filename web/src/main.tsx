import { StrictMode, useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import issuesData from './data/issues.json';
import './styles.css';

type Story = {
  index: number;
  title: string;
  region: string;
  category: string;
  summary: string;
  why: string;
  source: {
    name: string;
    url: string;
  };
  oneLiner: string;
};

type Issue = {
  date: string;
  number: string;
  title: string;
  intro: string;
  emailIntro?: string;
  issueFocus?: string;
  mainEditorial?: string;
  midRunNote?: string;
  perspective?: string;
  stories: Story[];
  assets: {
    hero: string;
    checkpoints: string;
  };
};

const issues = issuesData as Issue[];
const archiveDuckImage = '/assets/ducks/runeorrri-duck-03.svg';

function issuePath(issue: Issue) {
  return `/${issue.number}`;
}

function formatCategory(story: Story) {
  const regionLabel = story.region === 'korea' ? '국내' : story.region === 'global' ? '해외' : story.region;
  const categoryLabels: Record<string, string> = {
    event: '이벤트',
    race: '레이스',
    news: '뉴스',
    gear: '장비',
    elite: '엘리트',
    training: '훈련',
  };
  const categoryLabel = categoryLabels[story.category] || story.category;
  return `${regionLabel} / ${categoryLabel}`;
}

function InstagramIcon() {
  return (
    <svg className="brand-icon" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.5" cy="6.5" r="1.2" />
    </svg>
  );
}

function YouTubeIcon() {
  return (
    <svg className="brand-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M22 12s0-3.3-.4-4.9c-.2-.9-.9-1.6-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4c-.9.2-1.6.9-1.8 1.8C2 8.7 2 12 2 12s0 3.3.4 4.9c.2.9.9 1.6 1.8 1.8 1.6.4 7.8.4 7.8.4s6.2 0 7.8-.4c.9-.2 1.6-.9 1.8-1.8.4-1.6.4-4.9.4-4.9Z" />
      <path d="m10 15 5-3-5-3v6Z" />
    </svg>
  );
}

function App() {
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  const issueNumberMatch = path.match(/^\/(\d{2})$/);

  if (issueNumberMatch) {
    const issue = issues.find((item) => item.number === issueNumberMatch[1]);
    return issue ? <IssuePage issue={issue} /> : <NotFound />;
  }

  return <HomePage />;
}

function SubscribeModal({ onClose }: { onClose: () => void }) {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'duplicate' | 'error'>('idle');

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus('loading');
    try {
      const res = await fetch('/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      });
      if (res.ok) {
        setStatus('success');
      } else {
        const data = await res.json() as { error?: string };
        setStatus(data.error === 'already_subscribed' ? 'duplicate' : 'error');
      }
    } catch {
      setStatus('error');
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="닫기">✕</button>
        {status === 'success' ? (
          <div className="modal-success">
            <p className="eyebrow">SUBSCRIBED</p>
            <h2>구독이 완료됐습니다</h2>
            <p>매주 화/목/토에 러닝 소식을 전해드릴게요.</p>
          </div>
        ) : (
          <>
            <p className="eyebrow">RUNEORRRI BRIEFING</p>
            <h2>무료 구독</h2>
            <p>매주 화/목/토, 국내외 러닝 소식 5개를 이메일로 보내드립니다.</p>
            <form onSubmit={handleSubmit} className="subscribe-form">
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="이메일 주소를 입력하세요"
                required
                disabled={status === 'loading'}
                className="subscribe-input"
              />
              <button type="submit" disabled={status === 'loading'} className="subscribe-submit">
                {status === 'loading' ? '처리 중…' : '구독하기'}
              </button>
            </form>
            {status === 'duplicate' && <p className="subscribe-msg subscribe-msg--warn">이미 구독 중인 이메일입니다.</p>}
            {status === 'error' && <p className="subscribe-msg subscribe-msg--error">오류가 발생했습니다. 잠시 후 다시 시도해주세요.</p>}
          </>
        )}
      </div>
    </div>
  );
}

function Topbar() {
  const latest = issues[0];
  const [showModal, setShowModal] = useState(false);
  return (
    <>
      <header className="topbar">
        <div className="topbar-side topbar-left">
          {latest ? <a className="nav-link" href={issuePath(latest)}>최신호</a> : null}
          <button className="subscribe-btn" onClick={() => setShowModal(true)}>무료 구독</button>
        </div>
      <a className="brand" href="/" aria-label="runeorrri 홈">
        runeorrri
      </a>
      <div className="topbar-side topbar-right">
        <a
          href="https://www.instagram.com/runeorrri"
          target="_blank"
          rel="noreferrer"
          aria-label="Instagram에서 runeorrri 보기"
          className="nav-social"
        >
          <InstagramIcon />
        </a>
        <a
          href="https://youtube.com/@eorrri"
          target="_blank"
          rel="noreferrer"
          aria-label="YouTube에서 eorrri 보기"
          className="nav-social"
        >
          <YouTubeIcon />
        </a>
      </div>
      </header>
      {showModal && <SubscribeModal onClose={() => setShowModal(false)} />}
    </>
  );
}

function HomePage() {
  const [latest, ...previous] = issues;

  return (
    <main>
      <Topbar />
      {latest ? (
        <section className="home-hero">
          <div className="home-copy">
            <p className="eyebrow">RUNEORRRI BRIEFING</p>
            <h1>
              Running can
              <span className="title-line">change the world</span>
            </h1>
            <p className="home-description">
              러너리가 고른 국내외 러닝 소식을 한 번에 읽고, 필요한 원문만 바로 열어볼 수 있게
              정리합니다.
            </p>
            <a className="primary-link" href={issuePath(latest)}>
              오늘의 러닝 브리핑 {latest.number}
            </a>
          </div>
          <a className="hero-image-link" href={issuePath(latest)} aria-label="최신 브리핑 보기">
            <img src={latest.assets.hero} alt={`오늘의 러닝 브리핑 ${latest.number}`} />
          </a>
        </section>
      ) : (
        <EmptyState />
      )}

      <section className="issue-list-section" aria-label="뉴스레터 회차 목록">
        <div className="section-heading">
          <p className="eyebrow">ARCHIVE</p>
          <h2>지난 브리핑</h2>
        </div>
        <div className="issue-grid">
          {issues.map((issue) => (
            <a className="issue-card" href={issuePath(issue)} key={issue.date}>
              <div className="issue-card-copy">
                <p className="card-meta">{issue.date}, {issue.stories.length} stories</p>
                <h3>오늘의 러닝 브리핑 {issue.number}</h3>
                <ol>
                  {issue.stories.slice(0, 3).map((story) => (
                    <li key={story.index}>{story.title}</li>
                  ))}
                </ol>
              </div>
              <img className="issue-card-duck" src={archiveDuckImage} alt="" />
            </a>
          ))}
        </div>
        {previous.length === 0 ? <p className="quiet-note">다음 브리핑이 발행되면 여기에 차곡차곡 쌓입니다.</p> : null}
      </section>
    </main>
  );
}

function IssuePage({ issue }: { issue: Issue }) {
  const mainStory = issue.stories[0];
  const briefs = issue.stories.slice(1);

  return (
    <main>
      <Topbar />
      <article className="issue-page">
        <header className="issue-header">
          <p className="eyebrow">{issue.date}</p>
          <h1>오늘의 러닝 브리핑 {issue.number}</h1>
        </header>

        <img className="wide-art" src={issue.assets.hero} alt={`오늘의 러닝 브리핑 ${issue.number}`} />

        <section className="issue-intro">
          <p>{issue.intro}</p>
          {issue.issueFocus ? <p className="issue-focus">{issue.issueFocus}</p> : null}
        </section>

        <section className="lineup-section">
          <div className="lineup-box">
            <p className="lineup-box-label">오늘의 라인업</p>
            <ol className="lineup-list">
              {issue.stories.map((story) => (
                <li key={story.index} className="lineup-item">
                  <a href={`#story-${story.index}`} className="lineup-link">
                    <span className="lineup-meta">{String(story.index).padStart(2, '0')}, {formatCategory(story)}</span>
                    <span className="lineup-title">{story.title}</span>
                  </a>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {mainStory ? (
          <section className="main-story" id={`story-${mainStory.index}`}>
            <p className="eyebrow">MAIN STORY</p>
            <h2>{mainStory.title}</h2>
            <p>{mainStory.summary}</p>
            {issue.mainEditorial ? <p className="main-editorial">{issue.mainEditorial}</p> : null}
            <div className="comment-box">
              <b>러너리 코멘트</b>
              <span>{mainStory.why}</span>
            </div>
            <SourceLink story={mainStory} />
          </section>
        ) : null}

        {issue.midRunNote ? (
          <section className="mid-run-note">
            <p className="eyebrow">MID-RUN NOTE</p>
            <p>{issue.midRunNote}</p>
          </section>
        ) : null}

        {issue.perspective ? (
          <section className="perspective-section">
            <p className="perspective-label">이번 호를 읽는 관점</p>
            <p>{issue.perspective}</p>
          </section>
        ) : null}

        <section className="brief-list">
          <div className="section-heading">
            <p className="eyebrow">RUNEORRRI BRIEFS</p>
            <h2>나머지 소식</h2>
          </div>
          {briefs.map((story) => (
            <article className="brief-item" key={story.index} id={`story-${story.index}`}>
              <p className="story-meta">{String(story.index).padStart(2, '0')}, {formatCategory(story)}</p>
              <h3>{story.title}</h3>
              <p>{story.summary}</p>
              <div className="soft-comment">
                <b>러너리 코멘트</b>
                <span>{story.why}</span>
              </div>
              <SourceLink story={story} />
            </article>
          ))}
        </section>

        <section className="checkpoint-section">
          <div className="section-heading">
            <p className="eyebrow">CHECKPOINTS</p>
            <h2>체크포인트</h2>
          </div>
          <img className="wide-art" src={issue.assets.checkpoints} alt="러너리 체크포인트" />
        </section>

        <section className="sources-panel">
          <p className="eyebrow">SOURCES</p>
          {issue.stories.map((story) => (
            <a href={story.source.url} key={story.index} target="_blank" rel="noreferrer">
              {story.title}
              <span>{story.source.name}</span>
            </a>
          ))}
        </section>
      </article>
    </main>
  );
}

function SourceLink({ story }: { story: Story }) {
  if (!story.source.url) {
    return null;
  }
  return (
    <p className="source-link">
      원문:{' '}
      <a href={story.source.url} target="_blank" rel="noreferrer">
        {story.source.name}
      </a>
    </p>
  );
}

function NotFound() {
  return (
    <main>
      <Topbar />
      <section className="not-found">
        <p className="eyebrow">NOT FOUND</p>
        <h1>해당 브리핑을 찾을 수 없습니다</h1>
        <a className="primary-link" href="/">홈으로 돌아가기</a>
      </section>
    </main>
  );
}

function EmptyState() {
  return (
    <section className="not-found">
      <p className="eyebrow">EMPTY</p>
      <h1>아직 발행된 브리핑이 없습니다</h1>
    </section>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
