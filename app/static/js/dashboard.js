// 移动端适配检测
function isMobileDevice() {
    return window.innerWidth <= 768;
}

// 湖南工商大学作息时间表
const SCHOOL_SCHEDULE = {
    // 夏季时间 (5月1日起)
    summer: {
        south: { // 南校区
            '早自习': '7:20-7:50',
            '第一节课': '8:00-8:45',
            '第二节课': '8:55-9:40',
            '第三节课': '10:05-10:50',
            '第四节课': '11:00-11:45',
            '第五节课': '14:30-15:15',
            '第六节课': '15:20-16:05',
            '第七节课': '16:20-17:05',
            '第八节课': '17:10-17:55',
            '第九节课': '19:00-19:45',
            '第十节课': '19:50-20:35',
            '第十一节': '20:40-21:25',
            '第十二节': '21:30-22:15'
        },
        north: { // 北校区
            '早自习': '7:30-8:00',
            '第一节课': '8:10-8:55',
            '第二节课': '9:05-9:50',
            '第三节课': '10:05-10:50',
            '第四节课': '11:00-11:45',
            '第五节课': '14:30-15:15',
            '第六节课': '15:20-16:05',
            '第七节课': '16:15-17:00',
            '第八节课': '17:05-17:50',
            '第九节课': '19:00-19:45',
            '第十节课': '19:50-20:35',
            '第十一节': '20:40-21:25',
            '第十二节': '21:30-22:15'
        }
    },
    // 冬季时间 (10月1日起)
    winter: {
        south: { // 南校区
            '早自习': '7:20-7:50',
            '第一节课': '8:00-8:45',
            '第二节课': '8:55-9:40',
            '第三节课': '10:05-10:50',
            '第四节课': '11:00-11:45',
            '第五节课': '14:00-14:45',
            '第六节课': '14:50-15:35',
            '第七节课': '15:50-16:35',
            '第八节课': '16:40-17:25',
            '第九节课': '19:00-19:45',
            '第十节课': '19:50-20:35',
            '第十一节': '20:40-21:25',
            '第十二节': '21:30-22:15'
        },
        north: { // 北校区
            '早自习': '7:30-8:00',
            '第一节课': '8:10-8:55',
            '第二节课': '9:05-9:50',
            '第三节课': '10:05-10:50',
            '第四节课': '11:00-11:45',
            '第五节课': '14:00-14:45',
            '第六节课': '14:50-15:35',
            '第七节课': '15:45-16:30',
            '第八节课': '16:35-17:20',
            '第九节课': '19:00-19:45',
            '第十节课': '19:50-20:35',
            '第十一节': '20:40-21:25',
            '第十二节': '21:30-22:15'
        }
    }
};

// 获取当前季节和校区的时间表
function getCurrentSchedule(campus = 'south') {
    const now = new Date();
    const month = now.getMonth() + 1; // 月份从0开始，所以加1
    const day = now.getDate();
    
    // 判断是夏季还是冬季时间
    // 夏季时间：5月1日-9月30日
    // 冬季时间：10月1日-4月30日
    const isSummer = (month >= 5 && month <= 9) || (month === 10 && day < 1) || (month === 4 && day >= 30);
    const season = isSummer ? 'summer' : 'winter';
    
    return SCHOOL_SCHEDULE[season][campus];
}

// 根据节次获取对应的时间段
function getTimeSlotByPeriod(period, campus = 'south') {
    const schedule = getCurrentSchedule(campus);
    
    // 将课表中的节次格式转换为时间段
    const periodMap = {
        '第1-2节': ['第一节课', '第二节课'],
        '第3-4节': ['第三节课', '第四节课'],
        '第5-6节': ['第五节课', '第六节课'],
        '第7-8节': ['第七节课', '第八节课'],
        '第9-10节': ['第九节课', '第十节课'],
        '第11-12节': ['第十一节', '第十二节']
    };
    
    const periods = periodMap[period];
    if (periods && periods.length >= 2) {
        const startTime = schedule[periods[0]]?.split('-')[0];
        const endTime = schedule[periods[1]]?.split('-')[1];
        if (startTime && endTime) {
            return `${startTime}-${endTime}`;
        }
    }
    
    // 如果没有找到对应的时间段，返回默认值
    const defaultTimes = {
        '第1-2节': '08:00-09:40',
        '第3-4节': '10:00-11:40',
        '第5-6节': '14:00-15:40',
        '第7-8节': '16:00-17:40',
        '第9-10节': '19:00-20:40'
    };
    
    return defaultTimes[period] || '未知时间';
}

// 更新时间信息显示
function updateScheduleInfo() {
    const campusSelect = document.getElementById('campus-select');
    const scheduleInfoElement = document.getElementById('current-schedule-info');
    
    if (!campusSelect || !scheduleInfoElement) return;
    
    const selectedCampus = campusSelect.value;
    const campusName = selectedCampus === 'south' ? '南校区' : '北校区';
    
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    
    // 判断是夏季还是冬季时间
    const isSummer = (month >= 5 && month <= 9) || (month === 10 && day < 1) || (month === 4 && day >= 30);
    const seasonName = isSummer ? '夏季' : '冬季';
    
    scheduleInfoElement.textContent = `${seasonName}作息时间 · ${campusName}`;
}

// 移动端优化
function optimizeForMobile() {
    if (isMobileDevice()) {
        // 阻止双击缩放
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        // 优化滚动体验
        document.body.style.webkitOverflowScrolling = 'touch';
        
        // 自动调整视口
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
        }
    }
}

// 获取当前学年学期
function getCurrentSemester() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // 月份从0开始
    
    // 判断当前学期
    // 9月-次年1月为第一学期，2月-8月为第二学期
    let academicYear, semester;
    
    if (currentMonth >= 9) {
        // 9月及以后，当前学年第一学期
        academicYear = currentYear;
        semester = 1;
    } else if (currentMonth >= 2) {
        // 2-8月，上一学年第二学期
        academicYear = currentYear - 1;
        semester = 2;
    } else {
        // 1月，当前学年第一学期（跨年）
        academicYear = currentYear - 1;
        semester = 1;
    }
    
    return `${academicYear}-${academicYear + 1}-${semester}`;
}

// 根据学号生成对应年级的学期列表
function generateSemestersByStudentId(studentId) {
    if (!studentId || studentId.length < 2) {
        return getDefaultSemesters();
    }
    
    // 提取入学年份（学号前两位）
    const gradePrefix = studentId.substring(0, 2);
    const gradeNumber = parseInt(gradePrefix);
    
    // 计算入学年份（20xx）
    let admissionYear;
    if (gradeNumber >= 0 && gradeNumber <= 30) {
        admissionYear = 2000 + gradeNumber;
    } else {
        return getDefaultSemesters();
    }
    
    // 生成4年的学期列表
    const semesters = [];
    for (let year = 0; year < 4; year++) {
        const currentYear = admissionYear + year;
        const nextYear = currentYear + 1;
        
        // 第一学期
        semesters.push({
            value: `${currentYear}-${nextYear}-1`,
            text: `${currentYear}-${nextYear}学年第一学期`
        });
        
        // 第二学期
        semesters.push({
            value: `${currentYear}-${nextYear}-2`,
            text: `${currentYear}-${nextYear}学年第二学期`
        });
    }
    
    return semesters;
}

// 获取默认学期列表（如果无法解析学号）
function getDefaultSemesters() {
    return [
        { value: "2024-2025-2", text: "2024-2025学年第二学期" },
        { value: "2024-2025-1", text: "2024-2025学年第一学期" },
        { value: "2023-2024-2", text: "2023-2024学年第二学期" },
        { value: "2023-2024-1", text: "2023-2024学年第一学期" },
        { value: "2022-2023-2", text: "2022-2023学年第二学期" },
        { value: "2022-2023-1", text: "2022-2023学年第一学期" }
    ];
}

// 从页面获取用户学号
function getCurrentStudentId() {
    // 从隐藏的学号元素获取学号
    const userIdElement = document.querySelector('.user-id');
    if (userIdElement) {
        return userIdElement.textContent.trim();
    }
    return null;
}

// 初始化学期下拉列表
function initializeSemesterSelects() {
    const studentId = getCurrentStudentId();
    const semesters = generateSemestersByStudentId(studentId);
    const currentSemester = getCurrentSemester();
    
    // 更新成绩查询的学期选择
    const scoreSelect = document.getElementById('score-semester');
    if (scoreSelect) {
        scoreSelect.innerHTML = '<option value="">全部学期</option>';
        semesters.forEach(semester => {
            const option = document.createElement('option');
            option.value = semester.value;
            option.textContent = semester.text;
            // 如果是当前学期，设置为默认选中
            if (semester.value === currentSemester) {
                option.selected = true;
            }
            scoreSelect.appendChild(option);
        });
    }
    
    // 更新课表查询的学期选择
    const scheduleSelect = document.getElementById('schedule-semester');
    if (scheduleSelect) {
        scheduleSelect.innerHTML = '';
        let hasCurrentSemester = false;
        
        semesters.forEach(semester => {
            const option = document.createElement('option');
            option.value = semester.value;
            option.textContent = semester.text;
            // 如果是当前学期，设置为默认选中
            if (semester.value === currentSemester) {
                option.selected = true;
                hasCurrentSemester = true;
            }
            scheduleSelect.appendChild(option);
        });
        
        // 如果当前学期不在列表中，选择第一个学期
        if (!hasCurrentSemester && semesters.length > 0) {
            scheduleSelect.options[0].selected = true;
        }
    }
}

// Toast通知功能
function closeToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.parentElement.remove();
        }, 300);
    }
}

function autoCloseToasts() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        // 3秒后自动关闭
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('fade-out');
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.parentElement.remove();
                    }
                }, 300);
            }
        }, 3000);
    });
}

// 切换标签页
document.addEventListener('DOMContentLoaded', function() {
    // 初始化移动端优化
    optimizeForMobile();
    
    // 自动关闭toast通知
    autoCloseToasts();
    
    // 监听窗口大小变化
    window.addEventListener('resize', function() {
        optimizeForMobile();
    });
    
    // 初始化学期下拉列表
    initializeSemesterSelects();
    
    // 更新时间信息显示
    updateScheduleInfo();
    
    // 监听校区选择变化
    document.getElementById('campus-select').addEventListener('change', function() {
        updateScheduleInfo();
    });
    // 切换标签页
    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 移除所有导航项的active类
            document.querySelectorAll('.nav-link').forEach(t => t.classList.remove('active'));
            // 移除所有内容区域的active类
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // 添加当前导航项的active类
            this.classList.add('active');
            // 显示对应的内容区域
            const tabId = this.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });
    
    // 成绩查询
    document.getElementById('query-scores').addEventListener('click', function() {
        const semester = document.getElementById('score-semester').value;
        const loadingElement = document.getElementById('scores-loading');
        const errorElement = document.getElementById('scores-error');
        const tableElement = document.getElementById('scores-table');
        const tableBodyElement = document.getElementById('scores-body');
        
        // 显示加载中
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';

        // 某些移动端场景下 tableElement 可能已被卡片视图替换移除
        if (tableElement) {
            tableElement.style.display = 'none';
        }
        if (tableBodyElement) {
            tableBodyElement.innerHTML = '';
        }
        
        console.log('正在查询成绩，学期:', semester);
        
        // 发送请求
        fetch(`/api/scores?semester=${semester}`)
            .then(response => {
                console.log('成绩查询响应状态:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP错误: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                loadingElement.style.display = 'none';
                console.log('成绩查询响应数据:', data);
                
                if (data.success) {
                    // 使用前端解析HTML
                    const htmlData = data.html;
                    if (!htmlData) {
                        throw new Error('服务器返回的HTML数据为空');
                    }
                    
                    // 可以在控制台输出HTML以便调试
                    // console.log('HTML数据:', htmlData.substring(0, 500) + '...');
                    
                    const parsedData = parseScoresHtml(htmlData);
                    // 计算并显示平均绩点
                    const gpaStats = computeGPAStats(parsedData);
                    showGPAInfo(semester, gpaStats);

                    // 如果选择了具体学期，需要再用全部成绩更新学年GPA
                    if (semester) {
                        updateYearGPA(semester).then(updatedStats => {
                            if (updatedStats) {
                                showGPAInfo(semester, updatedStats);
                            }
                        });
                    }
                    
                    // 渲染成绩表格
                    if (parsedData && parsedData.length > 0) {
                        console.log('解析到成绩数据:', parsedData);
                        
                        if (isMobileDevice()) {
                            // 移动端使用卡片布局
                            renderScoresCardView(parsedData);
                        } else {
                            // 桌面端使用表格布局
                            renderScoresTableView(parsedData);
                        }
                    } else {
                        errorElement.textContent = '未找到成绩数据或解析失败';
                        errorElement.style.display = 'block';
                        console.error('成绩解析失败或为空');
                    }
                } else {
                    errorElement.textContent = data.message || '查询失败';
                    errorElement.style.display = 'block';
                    console.error('成绩查询失败:', data.message);
                }
            })
            .catch(error => {
                loadingElement.style.display = 'none';
                errorElement.textContent = '网络错误，请重试: ' + error.message;
                errorElement.style.display = 'block';
                console.error('成绩查询异常:', error);
            });
    });
    
    // 课表查询
    document.getElementById('query-schedule').addEventListener('click', function() {
        const semester = document.getElementById('schedule-semester').value;
        const loadingElement = document.getElementById('schedule-loading');
        const errorElement = document.getElementById('schedule-error');
        const resultElement = document.getElementById('schedule-result');
        
        // 显示加载中
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';
        resultElement.innerHTML = '';
        
        // 发送请求获取原始课表数据
        fetch(`/api/schedule?semester=${semester}`)
            .then(response => response.json())
            .then(data => {
                loadingElement.style.display = 'none';
                
                if (data.success) {
                    // 在前端直接解析HTML
                    const htmlData = data.html;
                    const processedData = parseScheduleHtml(htmlData);
                    
                    // 渲染课表网格
                    renderScheduleGrid(processedData);
                    
                    // 同时渲染卡片视图
                    renderScheduleCardView(processedData);
                } else {
                    errorElement.textContent = data.message || '查询失败';
                    errorElement.style.display = 'block';
                }
            })
            .catch(error => {
                loadingElement.style.display = 'none';
                errorElement.textContent = '网络错误，请重试';
                errorElement.style.display = 'block';
                console.error('Error:', error);
            });
    });
    
    // 视图切换功能
    document.getElementById('grid-view-btn').addEventListener('click', function() {
        switchView('grid');
    });
    
    document.getElementById('card-view-btn').addEventListener('click', function() {
        switchView('card');
    });
});

/**
 * 解析成绩HTML页面
 * @param {string} html - HTML字符串
 * @return {Array} - 解析后的成绩数据数组
 */
function parseScoresHtml(html) {
    try {
        // 创建一个临时的DOM元素来解析HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // 查找成绩表格，教务系统返回的表格ID为dataList
        let table = doc.querySelector('table#dataList');
        
        // 如果没有找到指定ID的表格，尝试其他方法
        if (!table) {
            // 尝试查找特定类名的表格
            table = doc.querySelector('table.Nsb_r_list');
            
            if (!table) {
                // 如果仍然找不到，尝试找到包含成绩数据的表格
                const tables = doc.querySelectorAll('table');
                for (const t of tables) {
                    // 如果表格有足够的行，可能是成绩表格
                    if (t.querySelectorAll('tr').length > 2) {
                        table = t;
                        break;
                    }
                }
            }
        }
        
        if (!table) {
            console.error('未找到成绩表格');
            return [];
        }
        
        // 获取表头
        const headers = [];
        const headerRows = table.querySelectorAll('tr');
        
        if (headerRows.length > 0) {
            // 第一行通常是表头
            const headerRow = headerRows[0];
            // 尝试找th，如果没有则找td
            let headerCells = headerRow.querySelectorAll('th');
            
            if (headerCells.length === 0) {
                headerCells = headerRow.querySelectorAll('td');
            }
            
            headerCells.forEach(cell => {
                // 去除表头中可能的HTML标签，只保留文本
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = cell.innerHTML;
                headers.push(tempDiv.textContent.trim());
            });
        }
        
        // 获取成绩数据
        const scores = [];
        const dataRows = Array.from(table.querySelectorAll('tr')).slice(1); // 跳过表头行
        
        dataRows.forEach(row => {
            let cells = row.querySelectorAll('td');
            
            if (cells.length === 0) {
                // 如果没有td，尝试th
                cells = row.querySelectorAll('th');
            }
            
            if (cells.length > 0) {
                const scoreData = {};
                
                cells.forEach((cell, i) => {
                    if (i < headers.length) {
                        // 处理成绩单元格可能包含的链接
                        if (headers[i] === '成绩' && cell.querySelector('a')) {
                            scoreData[headers[i]] = cell.querySelector('a').textContent.trim();
                        } else {
                            scoreData[headers[i]] = cell.textContent.trim();
                        }
                    } else {
                        scoreData[`列${i+1}`] = cell.textContent.trim();
                    }
                });
                
                // 映射固定字段名
                if (!scoreData['开课学期'] && scoreData['序号']) {
                    // 为了与原始代码兼容，确保有这些关键字段
                    if (scoreData['课程名称'] === undefined && scoreData['4']) {
                        scoreData['课程名称'] = scoreData['4'];
                    }
                    if (scoreData['成绩'] === undefined && scoreData['5']) {
                        scoreData['成绩'] = scoreData['5'];
                    }
                    if (scoreData['学分'] === undefined && scoreData['6']) {
                        scoreData['学分'] = scoreData['6'];
                    }
                    if (scoreData['绩点'] === undefined && scoreData['8']) {
                        scoreData['绩点'] = scoreData['8'];
                    }
                    if (scoreData['开课学期'] === undefined && scoreData['2']) {
                        scoreData['开课学期'] = scoreData['2'];
                    }
                    if (scoreData['课程性质'] === undefined && scoreData['11']) {
                        scoreData['课程性质'] = scoreData['11'];
                    }
                }
                
                scores.push(scoreData);
            }
        });

        console.log('解析到成绩数据:', scores.length, '条');
        return scores;
    } catch (error) {
        console.error('解析成绩HTML异常:', error);
        return [];
    }
}

/**
 * 根据成绩数据计算平均绩点
 * @param {Array} scoreList - 解析后的成绩数组
 * @return {Object} - { semesterGPA: {...}, yearGPA: {...} }
 */
function computeGPAStats(scoreList) {
    const semesterStats = {};
    const yearStats = {};
    scoreList.forEach(item => {
        const credit = parseFloat(item['学分']);
        const gp = parseFloat(item['绩点']);
        if (isNaN(credit) || isNaN(gp) || credit === 0) return;
        const semesterKey = item['开课学期'] || '';
        if (semesterKey) {
            if (!semesterStats[semesterKey]) {
                semesterStats[semesterKey] = { credit: 0, point: 0 };
            }
            semesterStats[semesterKey].credit += credit;
            semesterStats[semesterKey].point += credit * gp;

            const parts = semesterKey.split('-');
            if (parts.length >= 3) {
                const yearKey = `${parts[0]}-${parts[1]}`;
                if (!yearStats[yearKey]) {
                    yearStats[yearKey] = { credit: 0, point: 0 };
                }
                yearStats[yearKey].credit += credit;
                yearStats[yearKey].point += credit * gp;
            }
        }
    });

    const semesterGPA = {};
    Object.keys(semesterStats).forEach(key => {
        const s = semesterStats[key];
        if (s.credit > 0) {
            semesterGPA[key] = (s.point / s.credit).toFixed(2);
        }
    });

    const yearGPA = {};
    Object.keys(yearStats).forEach(key => {
        const s = yearStats[key];
        if (s.credit > 0) {
            yearGPA[key] = (s.point / s.credit).toFixed(2);
        }
    });

    return { semesterGPA, yearGPA };
}

/**
 * 在页面显示GPA信息
 * @param {string} selectedSemester - 当前选择的学期（可能为空字符串）
 * @param {Object} gpaStats - computeGPAStats 返回的对象
 */
function showGPAInfo(selectedSemester, gpaStats) {
    const gpaElement = document.getElementById('gpa-stats');
    if (!gpaElement) return;

    let html = '';
    if (selectedSemester && gpaStats.semesterGPA[selectedSemester]) {
        // 显示本学期 GPA
        html += `本学期平均绩点：<strong>${gpaStats.semesterGPA[selectedSemester]}</strong>`;
        const yearKey = selectedSemester.split('-').slice(0, 2).join('-');
        if (gpaStats.yearGPA[yearKey]) {
            html += ` &nbsp;|&nbsp; 本学年平均绩点：<strong>${gpaStats.yearGPA[yearKey]}</strong>`;
        }
    } else {
        // 如果未选择具体学期，则显示总体 GPA
        const allGPAs = Object.values(gpaStats.semesterGPA).map(v => parseFloat(v));
        if (allGPAs.length) {
            const avg = (allGPAs.reduce((a, b) => a + b, 0) / allGPAs.length).toFixed(2);
            html = `平均绩点（全部课程）：<strong>${avg}</strong>`;
        }
    }

    if (html) {
        gpaElement.innerHTML = html;
        gpaElement.style.display = 'block';
    } else {
        gpaElement.style.display = 'none';
    }
}

/**
 * 解析课表HTML
 * @param {string} html - HTML字符串
 * @return {Object} - 结构化的课表数据
 */
function parseScheduleHtml(html) {
    try {
        // 创建一个临时的DOM元素来解析HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // 初始化结构化数据
        const processedData = createEmptySchedule();
        
        // 提取备注信息 - 使用原生JS方法替代jQuery的:contains选择器
        let remarksText = "";
        const thElements = doc.querySelectorAll('th');
        for (const th of thElements) {
            if (th.textContent.includes('备注')) {
                const nextCell = th.nextElementSibling;
                if (nextCell && nextCell.tagName === 'TD') {
                    remarksText = nextCell.textContent.trim();
                    break;
                }
            }
        }
        processedData.remarks_text = remarksText;
        
        // 查找课表表格
        let table = doc.querySelector('table#kbtable');
        if (!table) {
            // 尝试查找其他可能的课表表格
            const tables = doc.querySelectorAll('table');
            for (const t of tables) {
                if (t.querySelectorAll('tr').length > 5) { // 课表通常有多行
                    table = t;
                    break;
                }
            }
        }
        
        if (!table) {
            console.error('未找到课表');
            return processedData;
        }
        
        // 解析课表
        const rows = table.querySelectorAll('tr');
        if (rows.length < 2) {
            return processedData;
        }
        
        // 跳过表头行
        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            // 检查这一行是否是备注行
            if (row.querySelector('th') && row.querySelector('th').textContent.includes('备注')) {
                continue; // 跳过备注行，已单独处理
            }
            
            const cells = row.querySelectorAll('td, th');
            
            // 确定当前行对应的时间段
            let timeSlot = null;
            if (cells.length > 0) {
                const firstCell = cells[0];
                const firstCellText = firstCell.textContent.trim();
                
                // 根据第一个单元格文本确定时间段
                if (firstCellText.includes('0102')) {
                    timeSlot = "第1-2节";
                } else if (firstCellText.includes('0304')) {
                    timeSlot = "第3-4节";
                } else if (firstCellText.includes('0506')) {
                    timeSlot = "第5-6节";
                } else if (firstCellText.includes('0708')) {
                    timeSlot = "第7-8节";
                } else if (firstCellText.includes('0910') || firstCellText.includes('09-10')) {
                    timeSlot = "第9-10节";
                } else if (firstCellText.includes('1112') || firstCellText.includes('11-12')) {
                    timeSlot = "第9-10节"; // 有些学校11-12节也算入晚上时段
                }
            }
            
            if (!timeSlot) continue;
            
            // 解析每一天的课程
            for (let j = 1; j < Math.min(cells.length, 8); j++) {
                const cell = cells[j];
                const dayOfWeek = getDayOfWeekByIndex(j);
                
                // 解析单元格内的课程信息
                const courseInfo = parseCourseInfo(cell);
                if (courseInfo.length > 0) {
                    processedData[timeSlot][dayOfWeek] = courseInfo;
                }
            }
        }
        
        // 不再单独处理备注中的课程
        
        return processedData;
    } catch (error) {
        console.error('解析课表HTML异常:', error);
        return createEmptySchedule();
    }
}

/**
 * 解析备注中的课程信息
 * @param {string} remarkText - 备注文本
 * @return {Array} - 课程信息数组
 */
function parseRemarkCourses(remarkText) {
    const courses = [];
    
    if (!remarkText) return courses;
    
    // 按分号分割不同课程
    const courseParts = remarkText.split(';');
    courseParts.forEach(part => {
        const trimmedPart = part.trim();
        if (trimmedPart) {
            // 按逗号分割课程名和教师名
            const courseInfo = trimmedPart.split(',');
            const course = {
                name: courseInfo[0] ? courseInfo[0].trim() : '',
                teacher: courseInfo[1] ? courseInfo[1].trim() : '',
                room: '',
                weeks: '特殊安排'
            };
            
            if (course.name) {
                courses.push(course);
            }
        }
    });
    
    return courses;
}

/**
 * 根据索引获取星期几
 * @param {number} index - 星期索引（1-7）
 * @return {string} - 星期几的中文表示
 */
function getDayOfWeekByIndex(index) {
    const days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
    if (index >= 1 && index <= 7) {
        return days[index - 1];
    }
    return "周一"; // 默认返回周一
}

/**
 * 解析单元格中的课程信息
 * @param {HTMLElement} cell - 单元格元素
 * @return {Array} - 课程信息数组
 */
function parseCourseInfo(cell) {
    const courses = [];
    
    // 检查是否有课程
    if (!cell || !cell.textContent || cell.textContent.trim() === '&nbsp;' || cell.textContent.trim().length < 5) {
        return courses;
    }
    
    try {
        // 只查找kbcontent类的div（完整信息），忽略kbcontent1类
        const contentDivs = cell.querySelectorAll('.kbcontent');
        
        if (contentDivs.length > 0) {
            // 处理每个课程div
            contentDivs.forEach(div => {
                // 忽略空内容或隐藏的内容
                if (div.textContent.trim() === '&nbsp;' || div.textContent.trim() === '') {
                    return;
                }
                
                const course = {
                    name: '',
                    teacher: '',
                    room: '',
                    weeks: ''
                };
                
                // 获取课程名称（第一行文本，到第一个br前）
                let htmlContent = div.innerHTML;
                let firstLine = htmlContent.split('<br')[0];
                if (firstLine) {
                    const temp = document.createElement('div');
                    temp.innerHTML = firstLine;
                    course.name = temp.textContent.trim();
                }
                
                // 提取教师信息
                const teacherFont = div.querySelector('font[title="老师"]');
                if (teacherFont) {
                    course.teacher = teacherFont.textContent.trim();
                }
                
                // 提取教室信息
                const roomFont = div.querySelector('font[title="教室"]');
                if (roomFont) {
                    course.room = roomFont.textContent.trim();
                }
                
                // 提取周次信息
                const weekFont = div.querySelector('font[title="周次(节次)"]');
                if (weekFont) {
                    course.weeks = weekFont.textContent.trim();
                }
                
                // 如果提取到课程名，则添加到结果中
                if (course.name && course.name !== '&nbsp;') {
                    courses.push(course);
                }
            });
        } else {
            // 如果没有特定的div，则尝试从单元格直接提取
            const text = cell.textContent.trim();
            if (text && text !== '&nbsp;') {
                // 简单解析，提取第一行作为课程名称
                const lines = text.split('\n');
                const course = {
                    name: lines[0] || '',
                    teacher: '',
                    room: '',
                    weeks: ''
                };
                
                // 尝试从后续行提取更多信息
                lines.forEach(line => {
                    const lowerLine = line.toLowerCase();
                    if (lowerLine.includes('老师')) {
                        course.teacher = line.replace(/老师.*/, '').trim();
                    } else if (lowerLine.includes('教室') || lowerLine.includes('楼') || lowerLine.includes('室')) {
                        course.room = line.trim();
                    } else if (lowerLine.includes('周')) {
                        course.weeks = line.trim();
                    }
                });
                
                if (course.name) {
                    courses.push(course);
                }
            }
        }
    } catch (error) {
        console.error('解析课程单元格错误:', error);
    }
    
    return courses;
}

/**
 * 创建空的课表数据结构
 * @return {Object} - 空的课表结构
 */
function createEmptySchedule() {
    return {
        "第1-2节": {
            "周一": [], "周二": [], "周三": [], "周四": [], "周五": [], "周六": [], "周日": []
        },
        "第3-4节": {
            "周一": [], "周二": [], "周三": [], "周四": [], "周五": [], "周六": [], "周日": []
        },
        "第5-6节": {
            "周一": [], "周二": [], "周三": [], "周四": [], "周五": [], "周六": [], "周日": []
        },
        "第7-8节": {
            "周一": [], "周二": [], "周三": [], "周四": [], "周五": [], "周六": [], "周日": []
        },
        "第9-10节": {
            "周一": [], "周二": [], "周三": [], "周四": [], "周五": [], "周六": [], "周日": []
        },
        "remarks_text": ""
    };
}

// 渲染课表网格视图
function renderScheduleGrid(scheduleData) {
    const resultElement = document.getElementById('schedule-result');
    const campusSelect = document.getElementById('campus-select');
    const selectedCampus = campusSelect ? campusSelect.value : 'south';
    
    // 创建课表网格
    let html = '<div class="schedule-table-container">';
    html += '<table class="schedule-table">';
    
    // 表头
    html += '<thead>';
    html += '<tr>';
    html += '<th class="time-header">时间</th>';
    html += '<th>周一</th>';
    html += '<th>周二</th>';
    html += '<th>周三</th>';
    html += '<th>周四</th>';
    html += '<th>周五</th>';
    html += '<th>周六</th>';
    html += '<th>周日</th>';
    html += '</tr>';
    html += '</thead>';
    
    // 时间段定义 - 使用动态时间
    const timeSlots = [
        { period: '第1-2节', time: '0102节', timeRange: getTimeSlotByPeriod('第1-2节', selectedCampus) },
        { period: '第3-4节', time: '0304节', timeRange: getTimeSlotByPeriod('第3-4节', selectedCampus) },
        { period: '第5-6节', time: '0506节', timeRange: getTimeSlotByPeriod('第5-6节', selectedCampus) },
        { period: '第7-8节', time: '0708节', timeRange: getTimeSlotByPeriod('第7-8节', selectedCampus) },
        { period: '第9-10节', time: '0910节', timeRange: getTimeSlotByPeriod('第9-10节', selectedCampus) }
    ];
    
    // 检测是否是移动设备
    const isMobile = window.innerWidth <= 768;
    
    // 生成表格主体
    html += '<tbody>';
    timeSlots.forEach(slot => {
        html += '<tr>';
        
        // 时间单元格，根据设备调整显示内容
        html += `<td class="time-slot">`;
        if (isMobile) {
            // 移动设备上简化显示
            html += `<div class="period-number">${slot.time.replace('节', '')}</div>`;
            html += `<div class="time-range">${slot.timeRange.replace('-', '<br>')}</div>`;
        } else {
            html += `<div class="period-number">${slot.time}</div>`;
            html += `<div class="time-range">${slot.timeRange}</div>`;
        }
        html += `</td>`;
        
        ['周一', '周二', '周三', '周四', '周五', '周六', '周日'].forEach(day => {
            const courses = scheduleData[slot.period]?.[day] || [];
            html += `<td class="course-cell ${courses.length > 0 ? 'has-course' : 'empty-cell'}">`;
            
            courses.forEach((course, index) => {
                html += `<div class="course-block course-${index % 5}">`;
                html += `<div class="course-name">${course.name}</div>`;
                if (course.teacher) {
                    html += `<div class="course-teacher">${course.teacher}</div>`;
                }
                if (course.room) {
                    html += `<div class="course-room">${course.room}</div>`;
                }
                if (course.weeks) {
                    html += `<div class="course-time">${course.weeks}</div>`;
                }
                html += `</div>`;
            });
            
            html += '</td>';
        });
        
        html += '</tr>';
    });
    
    // 添加备注行（如果有）
    if (scheduleData.remarks_text && scheduleData.remarks_text.trim()) {
        html += '<tr class="remarks-row">';
        html += '<th class="remarks-header">备注</th>';
        html += `<td colspan="7" class="remarks-content">${scheduleData.remarks_text}</td>`;
        html += '</tr>';
    }
    
    html += '</tbody>';
    html += '</table>';
    html += '</div>';
    
    resultElement.innerHTML = html;
    console.log('课表渲染完成');
}

// 切换视图
function switchView(viewType) {
    const gridBtn = document.getElementById('grid-view-btn');
    const cardBtn = document.getElementById('card-view-btn');
    const gridView = document.getElementById('schedule-result');
    const cardView = document.getElementById('schedule-card-view');
    
    if (viewType === 'grid') {
        gridBtn.classList.add('active');
        cardBtn.classList.remove('active');
        gridView.style.display = 'block';
        cardView.style.display = 'none';
    } else {
        gridBtn.classList.remove('active');
        cardBtn.classList.add('active');
        gridView.style.display = 'none';
        cardView.style.display = 'block';
    }
}

// 渲染课表卡片视图
function renderScheduleCardView(scheduleData) {
    const cardViewElement = document.getElementById('schedule-card-view');
    
    // 检测是否是移动设备，移动设备默认显示卡片视图
    if (isMobileDevice()) {
        switchView('card');
    }
    
    // 获取今天是周几
    const today = new Date().getDay();
    const todayName = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][today];
    
    // 一周的天数
    const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
    
    let html = '<div class="schedule-cards">';
    
    // 为每一天创建卡片
    weekDays.forEach(day => {
        const isToday = day === todayName;
        const dayData = getDaySchedule(scheduleData, day);
        
        html += `<div class="day-card">`;
        html += `<div class="day-card-header ${isToday ? 'today' : ''}">${day}</div>`;
        html += `<div class="day-card-body">`;
        
        if (dayData.length > 0) {
            dayData.forEach(course => {
                html += `<div class="course-item">`;
                html += `<div class="course-time-badge">${course.timeSlot}</div>`;
                html += `<div class="course-title">${course.name}</div>`;
                html += `<div class="course-meta">`;
                
                if (course.teacher) {
                    html += `<div class="course-meta-item">`;
                    html += `<span class="icon">👨‍🏫</span>`;
                    html += `<span>${course.teacher}</span>`;
                    html += `</div>`;
                }
                
                if (course.room) {
                    html += `<div class="course-meta-item">`;
                    html += `<span class="icon">📍</span>`;
                    html += `<span>${course.room}</span>`;
                    html += `</div>`;
                }
                
                html += `</div>`;
                
                if (course.weeks) {
                    html += `<div class="course-weeks">${course.weeks}</div>`;
                }
                
                html += `</div>`;
            });
        } else {
            html += `<div class="no-courses">今天没有课程</div>`;
        }
        
        html += `</div>`;
        html += `</div>`;
    });
    
    // 添加备注信息
    if (scheduleData.remarks_text && scheduleData.remarks_text.trim()) {
        html += `<div class="day-card">`;
        html += `<div class="day-card-header">备注信息</div>`;
        html += `<div class="day-card-body">`;
        html += `<div class="course-item">`;
        html += `<div class="course-title">特殊安排</div>`;
        html += `<div class="course-meta-item">${scheduleData.remarks_text}</div>`;
        html += `</div>`;
        html += `</div>`;
        html += `</div>`;
    }
    
    html += '</div>';
    
    cardViewElement.innerHTML = html;
    console.log('课表卡片视图渲染完成');
}

/**
 * 渲染成绩表格视图（桌面端）
 */
function renderScoresTableView(parsedData) {
    const tableElement = document.getElementById('scores-table');
    const tableBodyElement = document.getElementById('scores-body');
    
    tableBodyElement.innerHTML = '';
    
    parsedData.forEach((score, index) => {
        const row = document.createElement('tr');
        
        // 根据成绩设置不同样式
        const scoreValue = parseFloat(score['成绩']);
        let scoreClass = '';
        if (!isNaN(scoreValue)) {
            if (scoreValue >= 90) {
                scoreClass = 'text-success';
            } else if (scoreValue >= 60) {
                scoreClass = 'text-warning';
            } else {
                scoreClass = 'text-danger';
            }
        }
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${score['开课学期'] || '-'}</td>
            <td>${score['课程名称'] || '-'}</td>
            <td class="${scoreClass}">${score['成绩'] || '-'}</td>
            <td>${score['学分'] || '-'}</td>
            <td>${score['绩点'] || '-'}</td>
            <td>${score['课程性质'] || '-'}</td>
        `;
        tableBodyElement.appendChild(row);
    });
    
    tableElement.style.display = 'table';
}

/**
 * 渲染成绩卡片视图（移动端）
 */
function renderScoresCardView(parsedData) {
    const resultElement = document.getElementById('scores-result');
    
    let html = '<div class="scores-card-container">';
    
    parsedData.forEach((score, index) => {
        const scoreValue = parseFloat(score['成绩']);
        let scoreClass = 'score-normal';
        let scoreIcon = '📊';
        
        if (!isNaN(scoreValue)) {
            if (scoreValue >= 90) {
                scoreClass = 'score-excellent';
                scoreIcon = '🌟';
            } else if (scoreValue >= 80) {
                scoreClass = 'score-good';
                scoreIcon = '👍';
            } else if (scoreValue >= 60) {
                scoreClass = 'score-pass';
                scoreIcon = '✅';
            } else {
                scoreClass = 'score-fail';
                scoreIcon = '❌';
            }
        }
        
        html += `
            <div class="score-card">
                <div class="score-card-header">
                    <div class="course-name">${score['课程名称'] || '-'}</div>
                    <div class="score-badge ${scoreClass}">
                        <span class="score-icon">${scoreIcon}</span>
                        <span class="score-value">${score['成绩'] || '-'}</span>
                    </div>
                </div>
                <div class="score-card-body">
                    <div class="score-meta-row">
                        <div class="score-meta-item">
                            <span class="meta-label">学期</span>
                            <span class="meta-value">${score['开课学期'] || '-'}</span>
                        </div>
                        <div class="score-meta-item">
                            <span class="meta-label">学分</span>
                            <span class="meta-value">${score['学分'] || '-'}</span>
                        </div>
                    </div>
                    <div class="score-meta-row">
                        <div class="score-meta-item">
                            <span class="meta-label">绩点</span>
                            <span class="meta-value">${score['绩点'] || '-'}</span>
                        </div>
                        <div class="score-meta-item">
                            <span class="meta-label">课程性质</span>
                            <span class="meta-value">${score['课程性质'] || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultElement.innerHTML = html;
}

// 获取某天的课程安排
function getDaySchedule(scheduleData, day) {
    const daySchedule = [];
    const campusSelect = document.getElementById('campus-select');
    const selectedCampus = campusSelect ? campusSelect.value : 'south';
    
    // 时间段定义 - 使用动态时间
    const timeSlots = [
        { period: '第1-2节', timeRange: getTimeSlotByPeriod('第1-2节', selectedCampus) },
        { period: '第3-4节', timeRange: getTimeSlotByPeriod('第3-4节', selectedCampus) },
        { period: '第5-6节', timeRange: getTimeSlotByPeriod('第5-6节', selectedCampus) },
        { period: '第7-8节', timeRange: getTimeSlotByPeriod('第7-8节', selectedCampus) },
        { period: '第9-10节', timeRange: getTimeSlotByPeriod('第9-10节', selectedCampus) }
    ];
    
    timeSlots.forEach(slot => {
        const courses = scheduleData[slot.period]?.[day] || [];
        courses.forEach(course => {
            daySchedule.push({
                ...course,
                timeSlot: slot.timeRange,
                period: slot.period
            });
        });
    });
    
    return daySchedule;
} 

// 全局缓存全部成绩的统计结果，避免重复请求
let cachedAllGPAStats = null;

/**
 * 获取全部成绩并返回 GPA 统计（带缓存）。
 * @return {Promise<Object>} resolve 为 computeGPAStats 的返回值
 */
function fetchAllGPAStats() {
    if (cachedAllGPAStats) {
        return Promise.resolve(cachedAllGPAStats);
    }
    return fetch('/api/scores?semester=')
        .then(resp => {
            if (!resp.ok) throw new Error(resp.status);
            return resp.json();
        })
        .then(data => {
            if (data.success && data.html) {
                const allParsed = parseScoresHtml(data.html);
                cachedAllGPAStats = computeGPAStats(allParsed);
                return cachedAllGPAStats;
            }
            throw new Error(data.message || '获取全部成绩失败');
        })
        .catch(err => {
            console.error('获取全部成绩异常:', err);
            return null;
        });
}

/**
 * 基于全部成绩更新指定学期对应学年的 GPA
 * @param {string} selectedSemester
 * @return {Promise<Object|null>} 返回新的 gpaStats，若失败返回 null
 */
function updateYearGPA(selectedSemester) {
    return fetchAllGPAStats();
} 