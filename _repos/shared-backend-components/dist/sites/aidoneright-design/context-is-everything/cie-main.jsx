/* global React, ReactDOM, PRODUCTS, BRAND, PORTFOLIO */
// AI Done Right - the holding-company / portfolio overview site.
// Three products you run (Teleon, Baltor, AIDevObserver) on one open Resource (OpenHubForAI).
// Plain, human copy: no em dashes, no arrow glyphs, no login (this is an overview site, not an app).

const { GROUP, ENTITIES, LAYERS, PORTS } = PORTFOLIO;
const E = (id) => ENTITIES[id];
const PRODUCT_IDS = (LAYERS.find((l) => l.id === 'product') || LAYERS[0]).items;
const RESOURCE_IDS = (LAYERS.find((l) => l.id === 'resource') || { items: [] }).items;
const ALL_SURFACE_IDS = PRODUCT_IDS.concat(RESOURCE_IDS);

// routes use a "#/name" hash; bare "#anchor" links stay in-page scrolls on the home page
function useRoute() {
  const read = () => { const h = (typeof location !== 'undefined' && location.hash) || ''; return (h.indexOf('#/') === 0 ? h.slice(2) : '') || 'home'; };
  const [route, setRoute] = React.useState(read);
  React.useEffect(() => {
    const on = () => { setRoute(read()); if (location.hash.indexOf('#/') === 0) window.scrollTo(0, 0); };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}

function Mark({ s = 26 }) {
  // three converging strata into a single point of trust (the family mark)
  return (
    <svg className="cie-logo-mk" viewBox="0 0 24 24" width={s} height={s} aria-hidden="true">
      <rect x="3" y="4.5" width="18" height="3" rx="1.5" fill="var(--cie-blue)" />
      <rect x="5.5" y="10.5" width="13" height="3" rx="1.5" fill="var(--cie-baltor)" />
      <rect x="8" y="16.5" width="8" height="3" rx="1.5" fill="var(--cie-openhubforai)" />
    </svg>
  );
}

function Top({ theme, onToggle }) {
  return (
    <header className="cie-top">
      <a className="cie-logo" href="#/"><Mark /><span className="cie-logo-name">{GROUP.short}</span></a>
      <span className="cie-spacer" />
      <nav className="cie-top-nav">
        <a href="#portfolio">Products</a>
        <a href="#fit">How it fits</a>
        <a href="#trust">Trust</a>
        <a href="#/about">About</a>
      </nav>
      <button className="cie-theme-toggle" onClick={onToggle} aria-label="Toggle light or dark theme" title="Toggle light or dark">
        {theme === 'dark' ? '☀' : '☾'}
      </button>
    </header>
  );
}

function Hero() {
  return (
    <section className="cie-hero" id="top">
      <div className="cie-wrap cie-hero-grid">
        <div>
          <div className="cie-eyebrow">The {GROUP.name} family</div>
          <h1>AI,<br /><span className="tint-blue">done right.</span></h1>
          <p className="cie-lede">
            A model is only as good as the context it works with. We build the governed products you
            actually run, on top of an open store of context, tools, and skills you can browse for
            yourself. One design system, one promise, and parts that fit together.
          </p>
          <div className="cie-cta">
            <a className="cie-btn" style={{ background: 'var(--cie-blue)', color: '#fff' }} href="#portfolio">See the products</a>
            <a className="cie-btn cie-btn-ghost" href="#fit">How it fits together</a>
          </div>
        </div>
        <div className="cie-hero-aside">
          {LAYERS.map((layer) => (
            <div className="cha-layer" key={layer.id}>
              <span className="cha-label">{layer.label}</span>
              <div className="cha-chips">
                {layer.items.map((id) => {
                  const e = E(id);
                  return <span className="cha-chip" key={id} style={{ '--ent': e.accent }}><span className="g">{e.glyph}</span>{e.name}</span>;
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EntityCard({ id, verb }) {
  const e = E(id);
  const live = e.status === 'live';
  const Tag = e.url ? 'a' : 'div';
  return (
    <Tag className={'oh-card cie-ent' + (e.url ? ' linkable' : '')}
      href={e.url || undefined} style={{ '--ent': e.accent }}>
      <div className="ent-top">
        <span className="ent-glyph">{e.glyph}</span>
        <span className={'ent-status s-' + e.status}>{e.status}</span>
      </div>
      <div className="ent-name">{e.wordmark}</div>
      <div className="ent-kind">{e.kind}</div>
      <p className="ent-blurb">{e.blurb}</p>
      <span className="ent-go">{live ? (verb || 'Open') + ' ' + e.name : e.status === 'private' ? 'In private preview' : 'Coming soon'}</span>
    </Tag>
  );
}

function Products() {
  return (
    <section className="cie-section" id="portfolio">
      <div className="cie-wrap">
        <div className="cie-kicker">The products</div>
        <h2>Three products you run, on one shared foundation.</h2>
        <div className="cie-body">
          Every surface is built from the same design kit, so they differ only in their accent and
          their words. Learn one and you have learned them all.
        </div>
        <div className="cie-fam cie-fam-3">
          {PRODUCT_IDS.map((id) => <EntityCard key={id} id={id} verb="Open" />)}
        </div>
      </div>
    </section>
  );
}

function Resources() {
  return (
    <section className="cie-section cie-section--alt" id="resources">
      <div className="cie-wrap">
        <div className="cie-kicker">Resources</div>
        <h2>One open store underneath it all.</h2>
        <div className="cie-body">
          OpenHubForAI is the open store of context, tools, skills, and harnesses that the products
          draw from. It is free to browse, and free to build on.
        </div>
        <div className="cie-fam cie-fam-1">
          {RESOURCE_IDS.map((id) => <EntityCard key={id} id={id} verb="Browse" />)}
        </div>
      </div>
    </section>
  );
}

// the architecture, told as the products fitting onto the open foundation
const FITS = [
  ['OpenHubForAI is the open foundation.', 'An open store of context, tools, skills, and harnesses, with one shared vocabulary of parts. Every product draws from it.'],
  ['Teleon is the runtime.', 'It turns an open ended agent task into a deterministic, eval gated capability, using templates and skills from the open store.'],
  ['Baltor governs the truth.', 'Managed, verified, provable context, powered by Teleon. It serves context an agent can trust, and proves it.'],
  ['AIDevObserver watches the usage.', 'It reviews how teams use AI coding agents, then sends each finding to the product that resolves it.'],
];
function HowItFits() {
  return (
    <section className="cie-section" id="fit">
      <div className="cie-wrap">
        <div className="cie-kicker">How it fits</div>
        <h2>Governed products, on an open foundation.</h2>
        <div className="cie-fits">
          {FITS.map(([h, p], i) => (
            <div className="cie-fit" key={h}>
              <span className="cie-fit-n">{String(i + 1).padStart(2, '0')}</span>
              <div><div className="cie-fit-h">{h}</div><p className="cie-fit-p">{p}</p></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const TRUST = [
  ['✓', 'Discovery is not trust', 'Anything we suggest is labeled as a suggestion. Only Baltor’s governed source serves the truth, and everything else is something to verify first.', 'var(--verified)'],
  ['⌘', 'One design system', 'Every surface is built from the same kit. The only things that change between products are the accent color and the words.', 'var(--cie-blue)'],
  ['⚿', 'Your keys stay yours', 'If you bring your own key, we use it for that one request and nothing more. We never store it, and we never write it to a log.', 'var(--cie-blue)'],
];
function Trust() {
  return (
    <section className="cie-section" id="trust">
      <div className="cie-wrap">
        <div className="cie-kicker">Trust</div>
        <div className="cie-trust">
          {TRUST.map(([icon, h, p, color]) => (
            <div className="oh-card oh-card--pad cie-trustcard" key={h}>
              <div className="cie-trust-i" style={{ color }}>{icon}</div>
              <h4>{h}</h4><p>{p}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Band() {
  return (
    <section className="cie-band">
      <div className="cie-wrap">
        <h2>Start with any surface.</h2>
        <p>They share a foundation, so the first one teaches you the rest.</p>
        <div className="cie-cta cie-band-cta">
          {ALL_SURFACE_IDS.map((id, i) => {
            const e = E(id);
            return (
              <a className={'cie-btn' + (i === 0 ? '' : ' cie-btn-ghost')} key={id}
                href={e.url} style={i === 0 ? { background: 'var(--cie-blue)', color: '#fff' } : { '--ent': e.accent }}>
                {e.name}
              </a>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  const cols = [
    ['Products', PRODUCT_IDS.map((id) => [E(id).wordmark, E(id).url])],
    ['Resources', RESOURCE_IDS.map((id) => [E(id).wordmark, E(id).url])],
    ['Company', [['About', '#/about'], ['Mission', '#/mission'], ['Contact', '#/contact']]],
    ['Legal', [['Privacy', '#/privacy'], ['Terms', '#/terms']]],
  ];
  return (
    <footer className="cie-foot">
      <div className="cie-wrap cie-foot-grid">
        <div>
          <div className="cie-logo" style={{ marginBottom: 8 }}><Mark s={22} /><span className="cie-foot-name">{GROUP.short}</span></div>
          <div className="cie-foot-tag">A model is only as good as the context it works with.</div>
        </div>
        <div className="cie-foot-cols">
          {cols.map(([h, links]) => (
            <div className="cie-foot-col" key={h}>
              <h5>{h}</h5>
              {links.map(([label, href]) => <a key={label} href={href}>{label}</a>)}
            </div>
          ))}
        </div>
      </div>
      <div className="cie-wrap cie-foot-legal">{GROUP.name}. {GROUP.mission}</div>
    </footer>
  );
}

function Home() {
  return <><Hero /><Products /><Resources /><HowItFits /><Trust /><Band /></>;
}

// shared shell for the standalone pages (About, Mission, Contact, Privacy, Terms)
function Page({ eyebrow, title, lede, children }) {
  return (
    <section className="cie-section cie-page" id="top">
      <div className="cie-wrap cie-prose">
        <div className="cie-kicker">{eyebrow}</div>
        <h1 className="cie-page-h1">{title}</h1>
        {lede && <p className="cie-page-lede">{lede}</p>}
        {children}
      </div>
    </section>
  );
}

function About() {
  return (
    <Page eyebrow="About" title="About AI Done Right"
      lede="A model is only as good as the context it works with. That one idea is the whole company.">
      <p>Models keep getting better and cheaper, and that is exactly why the model is no longer the hard
        part. The hard part is everything around it: the context you feed it, the tools it can reach, the
        skills it can call on, and the proof that any of it is actually correct.</p>
      <p>So that is what we build. Three governed products you run in production, all sitting on one open
        store of parts you can browse and build on yourself. One design system runs through all of them,
        so they feel like a single product even though each one does its own job.</p>
      <p>We would rather ship something small that is provably correct than something large you have to take
        on faith. That bias shows up everywhere in how we work.</p>
    </Page>
  );
}

function Mission() {
  return (
    <Page eyebrow="Mission" title="Our mission"
      lede="AI, done right. That is the whole thing in three words, so here is what we mean by it.">
      <p>Most teams adopt a tool because a README looked good, trust a number because a model sounded
        confident, and ship a change because it seemed to work. We think that is backwards. A suggestion is
        not the truth until something checks it. A result is not a capability until it survives a real test.
        A key you hand us is not ours to keep.</p>
      <p>Our job is to make the trustworthy path the easy path: verified context, proven capabilities,
        honest receipts, and an open foundation anyone can read. If we do it right, doing AI the careful way
        stops being extra work and simply becomes the default.</p>
    </Page>
  );
}

function Contact() {
  return (
    <Page eyebrow="Contact" title="Contact us"
      lede="We would love to hear from you, whether you are kicking the tires, stuck on something, or want to talk about working together.">
      <p>The fastest way to reach us is email. We read everything that comes in and try to reply within a
        couple of business days.</p>
      <ul className="cie-contact">
        <li><b>General</b><span><a href="mailto:hello@aidoneright.dev">hello@aidoneright.dev</a></span></li>
        <li><b>Security</b><span><a href="mailto:security@aidoneright.dev">security@aidoneright.dev</a></span></li>
        <li><b>Privacy</b><span><a href="mailto:privacy@aidoneright.dev">privacy@aidoneright.dev</a></span></li>
      </ul>
      <p>If you found a security issue, please use the security address so it reaches the right people
        quickly. We will work with you to get it fixed.</p>
    </Page>
  );
}

function Privacy() {
  return (
    <Page eyebrow="Legal" title="Privacy policy" lede="Last updated June 2026.">
      <p>This policy explains what we collect, why, and what we do with it. The short version: we collect as
        little as we can, we never sell it, and a key you bring stays yours.</p>
      <h3>What we collect</h3>
      <p>When you visit our sites we keep basic, standard web logs, such as the pages you opened and roughly
        where the request came from, so we can keep the service running and spot abuse. If you contact us, we
        keep what you send so we can reply.</p>
      <h3>Bring your own keys</h3>
      <p>If you give one of our products an API key for a model or a service, we use it only for the request
        you asked for. We do not store it, and we do not write it to a log. When the request is done, it is
        gone.</p>
      <h3>What we do not do</h3>
      <p>We do not sell your data. We do not share it with advertisers. We do not use the contents of your
        private context to train models.</p>
      <h3>Your choices</h3>
      <p>You can ask us what we hold about you, ask us to correct it, or ask us to delete it. Write to
        <a href="mailto:privacy@aidoneright.dev"> privacy@aidoneright.dev</a> and we will take care of it.</p>
      <h3>Changes</h3>
      <p>If we change this policy in a meaningful way, we will update the date above and, where it matters,
        tell you directly.</p>
    </Page>
  );
}

function Terms() {
  return (
    <Page eyebrow="Legal" title="Terms of service" lede="Last updated June 2026.">
      <p>By using our sites and products, you agree to these terms. We have tried to keep them short and
        readable.</p>
      <h3>Using the service</h3>
      <p>You may use our products for any lawful purpose. Please do not try to break, overload, or reverse
        the service, and do not use it to harm others. If you are using it for a company, you are telling us
        you have the authority to accept these terms for them.</p>
      <h3>Your content</h3>
      <p>Anything you bring stays yours. You give us only the permission we need to run the service for you,
        and nothing more. You are responsible for making sure you have the right to use whatever you upload or
        connect.</p>
      <h3>The open parts</h3>
      <p>Parts of what we publish are open and free to build on under their stated licenses. Those licenses,
        not these terms, govern how you use the open pieces.</p>
      <h3>No false guarantees</h3>
      <p>We work hard to make the products correct and reliable, but we provide them as they are. Where a
        product marks something as a candidate or a suggestion, treat it as something to verify, not as
        settled truth.</p>
      <h3>Liability</h3>
      <p>To the extent the law allows, we are not liable for indirect or incidental losses that come from
        using the service. Nothing here limits rights you have that cannot be waived.</p>
      <h3>Changes and contact</h3>
      <p>We may update these terms as the products grow. If we make a significant change, we will update the
        date above. Questions go to <a href="mailto:hello@aidoneright.dev">hello@aidoneright.dev</a>.</p>
    </Page>
  );
}

const PAGES = { about: About, mission: Mission, contact: Contact, privacy: Privacy, terms: Terms };

function App() {
  const route = useRoute();
  const [theme, setTheme] = React.useState(() => {
    try { const s = localStorage.getItem('cie-theme'); if (s === 'light' || s === 'dark') return s; } catch (e) {}
    return 'light';  // default to bright mode across every site; the toggle still switches to dark
  });
  React.useEffect(() => { try { localStorage.setItem('cie-theme', theme); } catch (e) {} }, [theme]);
  const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  const PageComp = PAGES[route];
  return (
    <div className={'oh dir-s theme-' + theme + ' cie'}
      style={{ '--cie-baltor': E('baltor').accent, '--cie-openhubforai': E('openHubForAI').accent }}>
      <Top theme={theme} onToggle={toggle} />
      {PageComp ? <PageComp /> : <Home />}
      <Footer />
    </div>
  );
}
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
