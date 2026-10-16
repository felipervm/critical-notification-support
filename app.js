(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const text = (id, value) => { get(id).textContent = value; };
  const all = selector => [...document.querySelectorAll(selector)];
  const labels = {
    expected_behavior: 'Confirmation rule',
    configuration_review: 'Configuration review',
    evidence_gap: 'Outcome unknown',
    customer_verification: 'Clarify delivery',
    needs_review: 'More evidence needed'
  };
  const shortLabels = {
    'C-01': 'Stopping rule', 'C-02': 'Contact record', 'C-03': 'Retry window',
    'C-04': 'Missing receipt', 'C-05': 'Delivery meaning'
  };
  const eventLabels = {
    accepted: 'Request accepted', confirmed: 'Recipient confirmed',
    followup_suppressed: 'Follow-up suppressed', invalid_contact: 'Invalid contact recorded',
    attempted: 'Delivery attempted', retry_planned: 'Retry planned',
    provider_handoff: 'Provider handoff recorded', receipt_checked: 'Provider receipt checked',
    provider_delivered: 'Provider marked delivered', ack_checked: 'Acknowledgement checked'
  };
  const boundaries = {
    expected_behavior: 'Verify the configured confirmation rule before explaining the stopped follow-up.',
    configuration_review: 'A configuration review should involve an authorized administrator. This trace does not establish a platform outage.',
    evidence_gap: 'Missing evidence does not establish a delivery failure or a platform outage.',
    customer_verification: 'Provider delivery status and human acknowledgement answer different questions.',
    needs_review: 'Keep the outcome open until the source evidence supports a conclusion.'
  };
  let findings = []; let selected = 0; let activeEvent = 0; let view = 'timeline';

  function showEvent(index) {
    activeEvent = index;
    const event = findings[selected].events[index];
    text('event-detail', JSON.stringify(event, null, 2));
    all('[data-event]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.event) === index)));
  }
  function show(index) {
    selected = index; const finding = findings[index];
    all('#tabs [data-recipient]').forEach((button, i) => {
      button.setAttribute('aria-selected', String(i === index)); button.tabIndex = i === index ? 0 : -1;
    });
    get('investigation-panel').setAttribute('aria-labelledby', `recipient-${finding.recipient_id}`);
    text('person', finding.recipient_id); text('kind', labels[finding.classification] || finding.classification.replaceAll('_', ' '));
    get('kind').dataset.kind = finding.classification;
    text('why', finding.explanation); text('next', finding.next_action);
    text('case-boundary', boundaries[finding.classification] || boundaries.needs_review);
    const timeline = get('events'); timeline.replaceChildren();
    finding.events.forEach((event, i) => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'event-row';
      button.dataset.event = String(i); button.setAttribute('aria-controls', 'event-detail');
      const time = document.createElement('time'); time.dateTime = event.at; time.textContent = event.at.slice(11, 19);
      const marker = document.createElement('span'); marker.className = 'event-marker'; marker.setAttribute('aria-hidden', 'true');
      const description = document.createElement('span'); description.className = 'event-description';
      const heading = document.createElement('strong'); heading.textContent = eventLabels[event.type] || event.type.replaceAll('_', ' ');
      const detail = document.createElement('span');
      const parts = [];
      if (event.channel) parts.push(event.channel.toUpperCase());
      if (event.result) parts.push(event.result.replaceAll('_', ' '));
      detail.textContent = parts.join(' / ') || 'Recorded in the fictional trace';
      description.append(heading, detail);
      const arrow = document.createElement('span'); arrow.className = 'event-arrow'; arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true');
      button.append(time, marker, description, arrow); button.addEventListener('click', () => showEvent(i)); timeline.append(button);
    });
    text('raw-trace', JSON.stringify({ recipient_id: finding.recipient_id, events: finding.events }, null, 2));
    if (finding.events.length) showEvent(finding.events.length - 1);
    else text('event-detail', 'No event evidence is available.');
    document.body.dataset.recipient = finding.recipient_id;
  }
  function setView(nextView) {
    view = nextView;
    all('[data-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
    get('timeline-view').hidden = view !== 'timeline'; get('raw-view').hidden = view !== 'raw';
  }
  all('[data-view]').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));

  async function load() {
    try {
      const response = await fetch(get('main').dataset.report, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const report = await response.json();
      if (!Array.isArray(report.findings) || !report.findings.length) throw new Error('No generated findings');
      findings = report.findings; text('case-id', report.case_id);
      const tabs = get('tabs');
      findings.forEach((finding, i) => {
        const button = document.createElement('button'); button.type = 'button'; button.id = `recipient-${finding.recipient_id}`;
        button.dataset.recipient = finding.recipient_id; button.setAttribute('role', 'tab');
        button.setAttribute('aria-controls', 'investigation-panel');
        const id = document.createElement('span'); id.textContent = finding.recipient_id;
        const label = document.createElement('span'); label.textContent = shortLabels[finding.recipient_id] || labels[finding.classification] || 'Review the trace';
        button.append(id, label); button.addEventListener('click', () => show(i));
        button.addEventListener('keydown', event => {
          let next;
          if (event.key === 'ArrowRight') next = (i + 1) % findings.length;
          if (event.key === 'ArrowLeft') next = (i + findings.length - 1) % findings.length;
          if (event.key === 'Home') next = 0;
          if (event.key === 'End') next = findings.length - 1;
          if (next === undefined) return;
          event.preventDefault(); show(next); all('#tabs [data-recipient]')[next].focus();
        }); tabs.append(button);
      });
      show(Math.max(0, findings.findIndex(finding => finding.recipient_id === 'C-04')));
      document.body.dataset.ready = 'notification-v2';
    } catch (error) {
      get('load-error').hidden = false;
      text('load-error', 'The generated report could not load. Open the source report or executive brief below to inspect the evidence.');
      get('investigation-panel').hidden = true; document.body.dataset.ready = 'report-unavailable';
    }
  }

  const navigation = get('navigation'); const toggle = document.querySelector('.menu-toggle');
  function closeMenu() { navigation.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); toggle.setAttribute('aria-label', 'Open navigation'); }
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    navigation.classList.toggle('is-open', open); toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  });
  navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { closeMenu(); toggle.focus(); } });
  document.addEventListener('click', event => { if (!document.querySelector('.site-header').contains(event.target)) closeMenu(); });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }
    }), { threshold: .08 });
    all('.section-heading,.investigation-layout,.decision-intro,.artifact-grid,.about-layout').forEach(element => observer.observe(element));
    const navObserver = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      navigation.querySelectorAll('a').forEach(link => {
        if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      });
    }), { rootMargin: '-15% 0px -65% 0px' });
    all('main section[id]').forEach(element => navObserver.observe(element));
  }
  load();
})();
