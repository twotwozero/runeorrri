import { StrictMode } from 'react';
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
    lineup: string;
    checkpoints: string;
  };
};

const issues = issuesData as Issue[];

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

function App() {
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  const issueNumberMatch = path.match(/^\/(\d{2})$/);
  const legacyDateMatch = path.match(/^\/issues\/(\d{4}-\d{2}-\d{2})$/);

  if (issueNumberMatch) {
    const issue = issues.find((item) => item.number === issueNumberMatch[1]);
    return issue ? <IssuePage issue={issue} /> : <NotFound />;
  }

  if (legacyDateMatch) {
    const issue = issues.find((item) => item.date === legacyDateMatch[1]);
    return issue ? <IssuePage issue={issue} /> : <NotFound />;
  }

  return <HomePage />;
}

function Topbar() {
  const latest = issues[0];
  return (
    <header className="topbar">
      <div className="topbar-side topbar-left">
        {latest ? <a className="nav-link" href={issuePath(latest)}>최신호</a> : null}
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
          className="nav-instagram"
        >
          <InstagramIcon />
        </a>
      </div>
    </header>
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
              <img src={issue.assets.hero} alt="" />
              <div>
                <p className="card-meta">{issue.date} · {issue.stories.length} stories</p>
                <h3>오늘의 러닝 브리핑 {issue.number}</h3>
                <ol>
                  {issue.stories.slice(0, 3).map((story) => (
                    <li key={story.index}>{story.title}</li>
                  ))}
                </ol>
              </div>
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
          <p>{issue.intro}</p>
          {issue.issueFocus ? <p className="issue-focus">{issue.issueFocus}</p> : null}
        </header>

        <img className="wide-art" src={issue.assets.hero} alt={`오늘의 러닝 브리핑 ${issue.number}`} />

        <section className="lineup-section">
          <div className="section-heading">
            <p className="eyebrow">TODAY'S LINEUP</p>
            <h2>오늘의 라인업</h2>
          </div>
          <img className="wide-art" src={issue.assets.lineup} alt="오늘의 라인업" />
        </section>

        {mainStory ? (
          <section className="main-story">
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
            <article className="brief-item" key={story.index}>
              <p className="story-meta">{String(story.index).padStart(2, '0')} · {formatCategory(story)}</p>
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
