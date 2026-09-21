/** Report page behaviour: mounts the Executive Shell from the embedded JSON. */
import { mountExecShell } from './exec-shell.js';

const data = JSON.parse(document.getElementById('report-data').textContent);

const shell = mountExecShell({
  title: 'Mars News & Weather',
  tagline: 'The web-scraping exercise rebuilt as a scheduled pipeline: tested parsers over two static sources, a snapshot JSON the scraper commits, and a dashboard generated from it — Curiosity REMS weather by Martian month, the coldest and warmest months, pressure extremes, and a Martian year measured from the data. No database, no server.',
  repo: 'https://github.com/Freddricklogan/WebScraping-Mars',
  pagesUrl: 'https://freddricklogan.github.io/WebScraping-Mars/',
  badges: [{ label: 'Scheduled scrape', tone: 'accent' }, { label: 'Snapshot fallback', dot: true }, { label: 'Parsers tested on fixtures', dot: true }],
  kpis: [
    { label: 'Weather observations', compute: () => data.observations.toLocaleString(), tone: 'accent' },
    { label: 'Coldest / warmest month', compute: () => `${data.coldest} / ${data.warmest}` },
    { label: 'Martian year (measured)', compute: () => `${data.yearDays.toFixed(1)} days`, tone: 'ok' },
    { label: 'Articles', compute: () => data.articles },
    { label: 'Data from', compute: () => data.provenance.startsWith('live') ? 'live scrape' : 'committed snapshot', tone: 'muted' }
  ],
  tour: [
    { selector: '.md-note', title: 'Where the numbers come from', body: `This build used ${data.provenance}, fetched ${data.fetchedAt}. The scheduled workflow refreshes the snapshot weekly; if a source is unreachable the page says so and uses the last good snapshot.` },
    { selector: '#s-weather', title: 'The classic questions, computed', body: `Month ${data.coldest} is coldest and month ${data.warmest} warmest by mean minimum temperature; pressure is lowest in month ${data.lowestPressure} and highest in month ${data.highestPressure}. The Martian year comes out at ${data.yearDays.toFixed(1)} Earth days from the spacing of Ls = 0 crossings; the accepted value is 686.98.` },
    { selector: '#s-news', title: 'News, parsed not pasted', body: 'Fifteen articles with their dates and teasers, parsed from the source page by a function that fails loudly when the structure changes.' }
  ]
});
shell.refreshKpis();
