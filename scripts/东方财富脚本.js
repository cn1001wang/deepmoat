(function() {
    function tableToCSV(tableId) {
        const table = document.getElementById(tableId) || document.querySelector('.report_table table');
        if (!table) {
            console.error('未找到指定的表格');
            return null;
        }

        const rows = table.querySelectorAll('tr');
        const csv = [];
        
        // 提取表头
        const headerTable = document.querySelector('.tableHeaderFix');
        if (headerTable) {
            const headerRows = headerTable.querySelectorAll('tr');
            headerRows.forEach(row => {
                const cols = row.querySelectorAll('th, td');
                const rowData = [];
                cols.forEach(col => {
                    rowData.push('"' + col.innerText.trim().replace(/"/g, '""') + '"');
                });
                csv.push(rowData.join(','));
            });
        }

        // 提取正文内容
        rows.forEach(row => {
            // 排除隐藏行
            if (row.style.display === 'none') return;
            
            const cols = row.querySelectorAll('th, td');
            const rowData = [];
            cols.forEach(col => {
                // 处理可能存在的特殊字符
                let text = col.innerText.trim();
                // 移除换行符和多余空格
                text = text.replace(/\s+/g, ' ');
                rowData.push('"' + text.replace(/"/g, '""') + '"');
            });
            if (rowData.length > 0) {
                csv.push(rowData.join(','));
            }
        });

        return csv.join('\n');
    }

    function downloadCSV(csv, filename) {
        const csvFile = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
        const downloadLink = document.createElement('a');
        downloadLink.download = filename;
        downloadLink.href = window.URL.createObjectURL(csvFile);
        downloadLink.style.display = 'none';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }

    // 执行下载
    const title = document.querySelector('.report_title')?.innerText.trim() || '东方财富数据导出';
    const csvContent = tableToCSV();
    if (csvContent) {
        downloadCSV(csvContent, `${title}.csv`);
        console.log('导出成功！');
    }
})();
