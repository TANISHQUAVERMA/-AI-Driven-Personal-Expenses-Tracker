// =========================
// DEFAULT THEME → DARK
// =========================
document.body.classList.add("dark");

// =========================
// LOAD CATEGORY DROPDOWN
// =========================
const categoryDropdown = document.getElementById("categoryDropdown");
fetch("/api/categories")
    .then(r => r.json())
    .then(cats => {
        if (categoryDropdown) {
            categoryDropdown.innerHTML =
                "<option value=''>Select Category</option>" +
                cats.map(c => `<option value="${c.name}">${c.icon} ${c.name}</option>`).join("");
        }
    });

// =========================
// INITIAL LOAD
// =========================
loadTx();

async function loadTx() {
    const res = await fetch("/api/transactions");
    const rows = await res.json();

    renderList(rows);
    renderTable(rows);
    renderCharts(rows);
}

// =========================
// ADD NEW EXPENSE
// =========================
const txForm = document.getElementById("txForm");
if (txForm) {
    txForm.addEventListener("submit", async e => {
        e.preventDefault();

        const payload = {
            date: document.getElementById("date").value,
            description: document.getElementById("description").value,
            merchant: document.getElementById("merchant").value,
            amount: document.getElementById("amount").value,
            category: categoryDropdown.value
        };

        if (!payload.amount || !payload.description) {
            alert("Description & Amount required!");
            return;
        }

        await fetch("/api/transactions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        txForm.reset();
        loadTx();
    });
}

// =========================
// RECENT TRANSACTIONS
// =========================
function renderList(rows) {
    const txList = document.getElementById("txList");
    if (!txList) return;

    txList.innerHTML = rows
        .slice(0, 5)
        .map(r => `
            <div class="card" style="font-size:17px; padding:15px;">
                <b style="color:#00C6FF;">${r.amount}</b>
                <span style="opacity:0.9;"> — ${r.description}</span>
                <div style="margin-top:6px; font-size:16px; color:#00C6FF;">
                    Amount: ₹${r.merchant}
                </div>
            </div>
        `)
        .join("");
}

// =========================
// DELETE TRANSACTION
// =========================
async function deleteTx(id) {
    await fetch(`/api/transactions?id=${id}`, { method: "DELETE" });
    loadTx();
}

// =========================
// HISTORY TABLE
// =========================
function renderTable(rows) {
    const tbody = document.querySelector("#txTable tbody");
    if (!tbody) return;

    tbody.innerHTML = rows
        .map(r => `
        <tr>
            <td>${r.date}</td>
            <td>${r.description}</td>
            <td>₹${r.merchant}</td>
            <td>${r.amount}</td>
            <td>${r.category}</td>
            <td><button onclick="deleteTx(${r.id})">🗑</button></td>
        </tr>
        `)
        .join("");
}

// =========================
// CHART HANDLING
// =========================
let pieChartObj, lineChartObj;

function renderCharts(rows) {
    // No data? Stop rendering
    if (!rows || rows.length === 0) return;

    // CATEGORY DATA
    const byCat = {};
    rows.forEach(r => {
        byCat[r.category] = (byCat[r.category] || 0) + Number(r.amount);
    });

    // MONTHLY DATA
    const byMonth = {};
    rows.forEach(r => {
        const m = r.date.slice(0, 7);  // YYYY-MM
        byMonth[m] = (byMonth[m] || 0) + Number(r.amount);
    });

    // =========================
    // DESTROY OLD CHARTS
    // =========================
    if (pieChartObj) pieChartObj.destroy();
    if (lineChartObj) lineChartObj.destroy();

    // PIE CHART
    const pieCtx = document.getElementById("pieChart");
    pieChartObj = new Chart(pieCtx, {
        type: "pie",
        data: {
            labels: Object.keys(byCat),
            datasets: [{
                data: Object.values(byCat),
                backgroundColor: [
                    "#0098FF", "#66BB6A", "#FF7043", "#AA47BC", "#FFD54F"
                ]
            }]
        }
    });

    // LINE CHART
    const lineCtx = document.getElementById("lineChart");
    lineChartObj = new Chart(lineCtx, {
        type: "line",
        data: {
            labels: Object.keys(byMonth),
            datasets: [{
                label: "Monthly Spend",
                data: Object.values(byMonth),
                borderColor: "#00B4FF",
                backgroundColor: "rgba(0,180,255,0.15)",
                tension: 0.35,
                borderWidth: 3
            }]
        }
    });
}
