export default function PartyTable({ data }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead className="bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 uppercase text-xs">
          <tr>
            <th className="px-4 py-3">Party</th>
            <th className="px-4 py-3 text-right">Amount (₹)</th>
            <th className="px-4 py-3 text-right">Share (%)</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200 dark:divide-zinc-700">
          {data.map((row, i) => (
            <tr key={i} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
              <td className="px-4 py-3 font-medium text-zinc-900 dark:text-zinc-100">{row.party_name}</td>
              <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">
                ₹{Number(row.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right text-zinc-700 dark:text-zinc-300">{row.percentage}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}