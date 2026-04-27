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
  cardCopy: string;
};

type Issue = {
  date: string;
  number: string;
  title: string;
  intro: string;
  stories: Story[];
  assets: {
    hero: string;
    lineup: string;
    checkpoints: string;
  };
};

const issues = issuesData as Issue[];

function issuePath(issue: Issue) {
  return `/issues/${issue.date}`;
}

function formatCategory(story: Story) {
  return `${story.region || '소식'} / ${story.category || 'running'}`;
}

function App() {
  const path = window.location.pathname.replace(/\/$/, '') || '/';
  const issueMatch = path.match(/^\/issues\/(\d{4}-\d{2}-\d{2})$/);

  if (issueMatch) {
    const issue = issues.find((item) => item.date === issueMatch[1]);
    return issue ? <IssuePage issue={issue} /> : <NotFound />;
  }

  return <HomePage />;
}

function Topbar() {
  const latest = issues[0];
  return (
    <header className="topbar">
      <a className="brand" href={latest ? issuePath(latest) : '/'}>
        @runeorrri
      </a>
      <nav className="nav" aria-label="주요 메뉴">
        <a href="/">브리핑</a>
        {latest ? <a href={issuePath(latest)}>최신호</a> : null}
      </nav>
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
            <p className="eyebrow">RUNNERI BRIEFING</p>
            <h1>오늘 달리기 전에 볼 것들.</h1>
            <p>
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
            <div className="comment-box">
              <b>러너리 코멘트</b>
              <span>{mainStory.why}</span>
            </div>
            <SourceLink story={mainStory} />
          </section>
        ) : null}

        <section className="brief-list">
          <div className="section-heading">
            <p className="eyebrow">RUNNERI BRIEFS</p>
            <h2>나머지 소식</h2>
          </div>
          {briefs.map((story) => (
            <article className="brief-item" key={story.index}>
              <p className="story-meta">{String(story.index).padStart(2, '0')} · {formatCategory(story)}</p>
              <h3>{story.title}</h3>
              <p>{story.summary}</p>
              <div className="soft-comment">{story.why}</div>
              <SourceLink story={story} />
            </article>
          ))}
        </section>

        <section className="checkpoint-section">
          <div className="section-heading">
            <p className="eyebrow">CHECKPOINTS</p>
            <h2>이번 호에서 바로 할 일</h2>
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
