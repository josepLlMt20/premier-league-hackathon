import { useEffect, useState } from 'react';
import { fetchMatches, type MatchMetadata } from './api/client';
import { Viewer } from './features/viewer/Viewer';
import { Status } from './components/Status';
import { NativeSelect } from './components/ui/native-select';
import { copy } from './domain/copy';
import { readPreferences } from './domain/playback';
export function App() {
  const [matches, setMatches] = useState<readonly MatchMetadata[] | null>(null),
    [selected, setSelected] = useState('');
  const [error, setError] = useState(false),
    [attempt, setAttempt] = useState(0);
  const [language, setLanguage] = useState(() => readPreferences().language);
  const t = copy[language];
  useEffect(() => {
    const controller = new AbortController();
    let current = true;
    setError(false);
    void fetchMatches(controller.signal)
      .then((matches) => {
        if (current) {
          setMatches(matches);
          setSelected(matches[0]?.match_id || '');
        }
      })
      .catch(() => {
        if (current) setError(true);
      });
    return () => {
      current = false;
      controller.abort();
    };
  }, [attempt]);
  const metadata = matches?.find((match) => match.match_id === selected);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#match">
        {t.skip}
      </a>
      <header className="app-header">
        <span className="wordmark">
          Match<span>Context</span>
        </span>
        <span className="header-label">Inside the Game · Hackathon</span>
      </header>
      <main id="match">
        {error ? (
          <Status language={language} error retry={() => setAttempt((n) => n + 1)}>
            {t.unavailable}
          </Status>
        ) : !matches ? (
          <Status language={language}>{t.loading}</Status>
        ) : !matches.length ? (
          <Status language={language} retry={() => setAttempt((n) => n + 1)}>
            {t.empty}
          </Status>
        ) : (
          <>
            {matches.length > 1 && (
              <label className="match-selector" htmlFor="match-select">
                {t.match}
                <NativeSelect
                  id="match-select"
                  value={selected}
                  onChange={(e) => setSelected(e.target.value)}
                >
                  {matches.map((match) => (
                    <option key={match.match_id} value={match.match_id}>
                      {match.teams.map((team) => team.name).join(' · ')}
                    </option>
                  ))}
                </NativeSelect>
              </label>
            )}
            {metadata && (
              <Viewer key={metadata.match_id} metadata={metadata} onLanguageChange={setLanguage} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
