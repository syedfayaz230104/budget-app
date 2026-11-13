import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer
} from 'recharts';
import {
  getUsers, getSpendingByCategory, getMonthlyTrend,
  getBudgetComparison, getInsights, getRecurringSeries, generateData
} from './services/api';

const COLORS = ['#6366f1','#22d3ee','#f59e0b','#10b981','#ef4444',
                '#8b5cf6','#f97316','#14b8a6','#ec4899','#84cc16'];

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec'];

export default function App() {
  const [users,       setUsers]       = useState([]);
  const [userId,      setUserId]      = useState('');
  const [year,        setYear]        = useState(2026);
  const [month,       setMonth]       = useState(1);
  const [spending,    setSpending]    = useState([]);
  const [trend,       setTrend]       = useState([]);
  const [budgets,     setBudgets]     = useState([]);
  const [insights,    setInsights]    = useState([]);
  const [recurring,   setRecurring]   = useState([]);
  const [generating,  setGenerating]  = useState(false);
  const [genMsg,      setGenMsg]      = useState('');

  // Load user list on mount
  useEffect(() => {
    getUsers(0, 50).then(r => {
      setUsers(r.data);
      if (r.data.length > 0) setUserId(r.data[0].id);
    }).catch(() => {});
  }, []);

  // Load analytics when userId / year / month changes
  useEffect(() => {
    if (!userId) return;
    getSpendingByCategory(userId, year, month).then(r => setSpending(r.data)).catch(() => {});
    getMonthlyTrend(userId, year).then(r => {
      setTrend(r.data.map(d => ({ ...d, month: MONTHS[d.month - 1] })));
    }).catch(() => {});
    getBudgetComparison(userId, year, month).then(r => setBudgets(r.data)).catch(() => {});
    getInsights(userId).then(r => setInsights(r.data.slice(0, 10))).catch(() => {});
    // get accounts for recurring
    import('./services/api').then(({ getAccounts }) => {
      // fallback: derive primary account id
      const num = userId.replace('USR-', '');
      getRecurringSeries(`ACC-${num}-01`).then(r => setRecurring(r.data)).catch(() => {});
    });
  }, [userId, year, month]);

  const handleGenerate = () => {
    setGenerating(true);
    setGenMsg('Generating data... this may take a few minutes.');
    generateData(100, 500).then(r => {
      setGenMsg(r.data.message);
      setGenerating(false);
      // Reload users
      getUsers(0, 50).then(r => setUsers(r.data));
    }).catch(() => {
      setGenMsg('Error generating data. Check backend logs.');
      setGenerating(false);
    });
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="bg-indigo-700 shadow-lg px-8 py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-wide">🏦 YottaFlex Budget Dashboard</h1>
        <span className="text-indigo-200 text-sm">Hackathon 2026</span>
      </header>

      <main className="p-6 space-y-6 max-w-7xl mx-auto">

        {/* Controls */}
        <section className="bg-gray-900 rounded-xl p-5 flex flex-wrap gap-4 items-end shadow">
          <div>
            <label className="block text-xs text-gray-400 mb-1">User</label>
            <select
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
              value={userId}
              onChange={e => setUserId(e.target.value)}
            >
              {users.map(u => (
                <option key={u.id} value={u.id}>{u.id} – {u.first_name} {u.last_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Year</label>
            <select
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
              value={year} onChange={e => setYear(Number(e.target.value))}
            >
              {[2025,2026].map(y => <option key={y}>{y}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Month</label>
            <select
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm"
              value={month} onChange={e => setMonth(Number(e.target.value))}
            >
              {MONTHS.map((m,i) => <option key={m} value={i+1}>{m}</option>)}
            </select>
          </div>
          <div className="ml-auto flex flex-col items-end gap-1">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium"
            >
              {generating ? 'Generating…' : '⚡ Generate Synthetic Data'}
            </button>
            {genMsg && <p className="text-xs text-indigo-300">{genMsg}</p>}
          </div>
        </section>

        {/* KPI Cards */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Spent', value: `$${spending.reduce((s,c)=>s+c.total_spent,0).toLocaleString('en',{maximumFractionDigits:2})}` },
            { label: 'Categories', value: spending.length },
            { label: 'Budgets',    value: budgets.length },
            { label: 'Insights',   value: insights.length },
          ].map(k => (
            <div key={k.label} className="bg-gray-900 rounded-xl p-5 shadow text-center">
              <p className="text-xs text-gray-400 mb-1">{k.label}</p>
              <p className="text-2xl font-bold text-indigo-300">{k.value}</p>
            </div>
          ))}
        </section>

        {/* Charts Row 1 */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Spending by Category – Bar Chart */}
          <div className="bg-gray-900 rounded-xl p-5 shadow">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Spending by Category</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={spending} margin={{ top: 5, right: 10, left: 0, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="category_name" tick={{ fontSize: 10, fill: '#9ca3af' }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <Tooltip formatter={v => [`$${v.toFixed(2)}`, 'Spent']} contentStyle={{ backgroundColor:'#1f2937', border:'none' }} />
                <Bar dataKey="total_spent" radius={[4,4,0,0]}>
                  {spending.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Category Distribution – Pie Chart */}
          <div className="bg-gray-900 rounded-xl p-5 shadow">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Category Distribution</h2>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={spending} dataKey="total_spent" nameKey="category_name"
                     cx="50%" cy="50%" outerRadius={90} label={({ category_name }) => category_name}>
                  {spending.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={v => [`$${v.toFixed(2)}`]} contentStyle={{ backgroundColor:'#1f2937', border:'none' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Charts Row 2 */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Monthly Income vs Spending */}
          <div className="bg-gray-900 rounded-xl p-5 shadow">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Monthly Trend – Income vs Spending</h2>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ backgroundColor:'#1f2937', border:'none' }} />
                <Legend />
                <Line type="monotone" dataKey="total_income" stroke="#10b981" strokeWidth={2} dot={false} name="Income" />
                <Line type="monotone" dataKey="total_spent"  stroke="#ef4444" strokeWidth={2} dot={false} name="Spending" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Budget vs Actual */}
          <div className="bg-gray-900 rounded-xl p-5 shadow">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Budget vs Actual</h2>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={budgets} margin={{ top: 5, right: 10, left: 0, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="category_name" tick={{ fontSize: 10, fill: '#9ca3af' }} angle={-30} textAnchor="end" />
                <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ backgroundColor:'#1f2937', border:'none' }} />
                <Legend />
                <Bar dataKey="budgeted" fill="#6366f1" radius={[4,4,0,0]} name="Budgeted" />
                <Bar dataKey="spent"    fill="#f59e0b" radius={[4,4,0,0]} name="Spent" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Insights & Recurring */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Insights */}
          <div className="bg-gray-900 rounded-xl p-5 shadow">
            <h2 className="text-sm font-semibold text-gray-300 mb-3">Recent Insights</h2>
            {insights.length === 0
              ? <p className="text-xs text-gray-500">No insights found.</p>
              : <ul className="space-y-2">
                  {insights.map(ins => (
                    <li key={ins.id} className="flex gap-3 items-start text-xs">
                      <span className={`mt-0.5 h-2 w-2 rounded-full flex-shrink-0 ${
                        ins.severity === 'high' ? 'bg-red-500' :
                        ins.severity === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                      }`} />
                      <span className="text-gray-300">{ins.description}</span>
                    </li>
                  ))}
                </ul>
            }
          </div>

          {/* Recurring Series */}
          <div className="bg-gray-900 rounded-xl p-5 shadow">
            <h2 className="text-sm font-semibold text-gray-300 mb-3">Recurring Payments</h2>
            {recurring.length === 0
              ? <p className="text-xs text-gray-500">No recurring series found.</p>
              : <table className="w-full text-xs text-gray-300">
                  <thead>
                    <tr className="text-gray-500 border-b border-gray-700">
                      <th className="pb-1 text-left">Series ID</th>
                      <th className="pb-1 text-left">Category</th>
                      <th className="pb-1 text-right">Amount</th>
                      <th className="pb-1 text-left">Freq.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recurring.slice(0,8).map(r => (
                      <tr key={r.id} className="border-b border-gray-800 hover:bg-gray-800">
                        <td className="py-1">{r.id}</td>
                        <td className="py-1">{r.category_id}</td>
                        <td className={`py-1 text-right font-mono ${r.amount < 0 ? 'text-red-400' : 'text-green-400'}`}>
                          ${Math.abs(r.amount).toFixed(2)}
                        </td>
                        <td className="py-1">{r.frequency}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
            }
          </div>
        </section>

      </main>
    </div>
  );
}
