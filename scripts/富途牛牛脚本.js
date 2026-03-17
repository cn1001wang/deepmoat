(function () {
  const result = {
    dates: [],
    rows: []
  };

  // 1️⃣ 解析表头日期
  const dateNodes = document.querySelectorAll(
    ".data-head .number-value"
  );

  result.dates = Array.from(dateNodes).map(node =>
    node.innerText.trim()
  );

  // 2️⃣ 解析数据行
  const rows = document.querySelectorAll(".data-table .child-item");

  rows.forEach(row => {
    const nameNode = row.querySelector(".child-name, .first-title-text");
    if (!nameNode) return;

    const name = nameNode.innerText.trim();

    const valueNodes = row.querySelectorAll(".number-value");

    const values = Array.from(valueNodes).map(node => {
      const spans = node.querySelectorAll(".value-item");

      if (spans.length === 2) {
        return {
          yoy: spans[0].innerText.trim() || null,
          value: spans[1].innerText.trim() || null
        };
      }

      if (spans.length === 1) {
        return {
          yoy: null,
          value: spans[0].innerText.trim() || null
        };
      }

      return {
        yoy: null,
        value: null
      };
    });

    result.rows.push({
      name,
      values
    });
  });

  console.log(result);

  // 如果你想直接复制JSON
  copy(JSON.stringify(result, null, 2));

  return result;
})();
// todo
// 我想要做一个无头浏览器，可以访问富途牛牛例如我需要https://www.futunn.com/stock/600298-SH/financials-cash-flow
// https://www.futunn.com/stock/600298-SH/financials-balance-sheet
// https://www.futunn.com/stock/600298-SH/financials-income-statement
// 把这三张表的数据

const script = document.createElement("script");
script.src = "https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js";
document.body.appendChild(script);

script.onload = () => {
  html2canvas(document.querySelector(".reports"), {
    scale: 2,          // 清晰度（建议2）
    useCORS: true,
    backgroundColor: "#ffffff",
  ignoreElements: (element) => {
    return element.classList?.contains("filter-nav");
  }
  }).then(canvas => {
    const link = document.createElement("a");
    link.download = "table.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
  });
}
