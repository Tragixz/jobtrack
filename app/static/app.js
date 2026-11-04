const applicationsBody = document.getElementById("applications");
const statsSection = document.getElementById("stats");
const followUpsList = document.getElementById("follow-ups");
const statusFilter = document.getElementById("status-filter");

// Calls our API and returns the JSON response.
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

// Creates an HTML element with an optional class and text.
function el(tag, className, text) {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (text !== undefined) {
    element.textContent = text;
  }
  return element;
}

// Turns "2026-11-04" into a readable date like "11/4/2026".
function formatDate(value) {
  if (!value) {
    return "—";
  }
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function companyCell(application) {
  const td = el("td");
  const url = application.url;
  if (url && (url.startsWith("https://") || url.startsWith("http://"))) {
    const link = el("a", "", application.company);
    link.href = url;
    link.target = "_blank";
    td.append(link);
  } else {
    td.textContent = application.company;
  }
  return td;
}

function renderApplications(applications) {
  applicationsBody.replaceChildren();

  if (applications.length === 0) {
    const row = el("tr");
    const td = el("td", "empty", "No applications yet. Add one above!");
    td.colSpan = 6;
    row.append(td);
    applicationsBody.append(row);
    return;
  }

  for (const application of applications) {
    const statusCell = el("td");
    statusCell.append(el("span", `badge badge-${application.status}`, application.status));

    const row = el("tr");
    row.append(
      companyCell(application),
      el("td", "", application.role),
      statusCell,
      el("td", "", formatDate(application.applied_on)),
      el("td", "", formatDate(application.follow_up_on)),
      el("td"),
    );
    applicationsBody.append(row);
  }
}

function renderStats(stats) {
  const items = [
    ["Total", stats.total],
    ["Interviewing", stats.by_status.interviewing],
    ["Offers", stats.by_status.offer],
    ["Response rate", `${stats.response_rate}%`],
  ];

  statsSection.replaceChildren(
    ...items.map(([label, value]) => {
      const card = el("div", "stat");
      card.append(el("div", "stat-value", value), el("div", "stat-label", label));
      return card;
    }),
  );
}

function renderFollowUps(applications) {
  followUpsList.replaceChildren();

  if (applications.length === 0) {
    followUpsList.append(el("li", "muted", "Nothing due. Nice work!"));
    return;
  }

  for (const application of applications) {
    const text = `${application.company}: ${application.role} (due ${formatDate(application.follow_up_on)})`;
    followUpsList.append(el("li", "", text));
  }
}

// Loads everything from the API and redraws the page.
async function refresh() {
  const status = statusFilter.value;
  const query = status ? `?status=${status}` : "";

  try {
    const [applications, stats, followUps] = await Promise.all([
      api(`/applications${query}`),
      api("/stats"),
      api("/follow-ups"),
    ]);
    renderApplications(applications);
    renderStats(stats);
    renderFollowUps(followUps);
  } catch (error) {
    console.error(error);
    alert("Could not load your applications. Please try again.");
  }
}

statusFilter.addEventListener("change", refresh);
refresh();