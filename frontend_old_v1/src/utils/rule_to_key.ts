export const levelOne = [
    { label: "过低", value: "过低", desc: "low" },
    { label: "过高", value: "过高", desc: "high" },
]

export const levelTwo = [
    { label: "过小", value: "过小", desc: "low" },
    { label: "过大", value: "过大", desc: "high" },
]

export const levelThree = [
    { label: "过短", value: "过短", desc: "low" },
    { label: "过长", value: "过长", desc: "high" },
]

export const levelFour = [
    { label: "不合理", value: "不合理", desc: "worse" },
    // { label: "不良", value: "不良", desc: "low" },
]

export const levelFive = [
    { label: "不足", value: "不足", desc: "low" }
]

export const paraLevel = new Map([
    ["VP切换位置", levelOne],
    ["储料终止位置", levelOne],
    ["储料量", levelFive],

    ["压力", levelTwo],
    ["注射压力", levelTwo],
    ["保压压力", levelTwo],
    ["背压", levelTwo],

    ["温度", levelOne],
    ["料筒温度", levelOne],
    ["喷嘴温度", levelFour],
    ["下料口温度", levelFour],

    ["速度", levelTwo],
    ["注射速度", levelTwo],
    ["保压速度", levelTwo],
    ["螺杆转速", levelTwo],

    ["时间", levelThree],
    ["注射时间", levelThree],
    ["保压时间", levelThree],
    ["冷却时间", levelThree],

    ["注射位置", levelFour],
    ["位置", levelFour],
    ["锁模", levelFour]

])

export function getParaLevel(keyword: string) {
    return paraLevel.get(keyword)
}

export const normalKeyword = [
    {
        label: '位置',
        options: [
            { value: 'VP切换位置', label: 'VP切换位置', desc: 'VPTL' },
            { value: '储料终止位置', label: '储料终止位置', desc: 'MEL' },
            // { value: '储料量', label: '储料量', desc: 'MEL' },
            { value: '储后松退距离', label: '储后松退距离', desc: 'DDAM' },
            { value: '注射位置', label: '注射位置', desc: 'IPOS' },
            // { value: '分段位置', label: '分段位置', desc: 'FD' },
            { value: '残留量', label: '残留量', desc: 'CUSION' },
            // { value: '位置', label: '位置', desc: 'POS' }  
        ]
    },
    {
        label: '压力',
        options: [
            // { value: '压力', label: '压力', desc: 'PRES' },
            { value: '注射压力', label: '注射压力', desc: 'IP0' },
            { value: '保压压力', label: '保压压力', desc: 'PP0' },
            { value: '背压', label: '背压', desc: 'MBP0' }
        ]
    },
    {
        label: '温度',
        options: [
            // { value: '温度', label: '温度', desc: 'TEMP' },
            { value: '料筒温度', label: '料筒温度', desc: 'BT' },
            { value: '喷嘴温度', label: '喷嘴温度', desc: 'NT' },
            { value: '下料口温度', label: '下料口温度', desc: 'ET' },
        ]
    },
    {
        label: '速度',
        options: [
            // { value: '速度', label: '速度', desc: 'VEL' },
            { value: '注射速度', label: '注射速度', desc: 'IV0' },
            { value: '保压速度', label: '保压速度', desc: 'PV0' },
            { value: '螺杆转速', label: '螺杆转速', desc: 'MSR0' }
        ]
    },
    {
        label: '时间',
        options: [
            // { value: '时间', label: '时间', desc: 'TIME' },
            // { value: '周期时间', label: '周期时间', desc: 'CYCT' },
            { value: '注射时间', label: '注射时间', desc: 'IT' },
            { value: '保压时间', label: '保压时间', desc: 'PT0' },
            { value: '冷却时间', label: '冷却时间', desc: 'CT' }
        ]
    },    
    {
        label: '其他',
        options: [
            { value: '锁模', label: '锁模', desc: 'CLAMP' },
            // { value: '顶出力', label: '顶出力', desc: 'EFOR' },
            // { value: '开模速度', label: '开模速度', desc: 'OVEL' },
            // { value: '顶出速度', label: '顶出速度', desc: 'EVEL' }
        ]
    }
]

export const concludeKeyword = [
    {
        label: '位置',
        options: [
            { value: 'VP切换位置', label: 'VP切换位置', desc: 'VPTL' },
            { value: '储料终止位置', label: '储料终止位置', desc: 'MEL' },
            { value: '储后松退距离', label: '储后松退距离', desc: 'DDAM' },
            { value: '注射位置', label: '注射位置', desc: 'IPOS' },
            { value: '分段位置', label: '分段位置', desc: 'FD' },
            { value: '残留量', label: '残留量', desc: 'CUSION' },
        ]
    },
    {
        label: '压力',
        options: [
            { value: '注射压力', label: '注射压力', desc: 'IP0' },
            { value: '保压压力', label: '保压压力', desc: 'PP0' },
            { value: '背压', label: '背压', desc: 'MBP0' }
        ]
    },
    {
        label: '温度',
        options: [
            { value: '料筒温度', label: '料筒温度', desc: 'BT' },
            { value: '喷嘴温度', label: '喷嘴温度', desc: 'NT' },
            { value: '下料口温度', label: '下料口温度', desc: 'ET' },
        ]
    },
    {
        label: '速度',
        options: [
            { value: '注射速度', label: '注射速度', desc: 'IV0' },
            { value: '保压速度', label: '保压速度', desc: 'PV0' },
            { value: '螺杆转速', label: '螺杆转速', desc: 'MSR0' }
        ]
    },
    {
        label: '时间',
        options: [
            { value: '周期时间', label: '周期时间', desc: 'CYCT' },
            { value: '注射时间', label: '注射时间', desc: 'IT' },
            { value: '保压时间', label: '保压时间', desc: 'PT0' },
            { value: '冷却时间', label: '冷却时间', desc: 'CT' }
        ]
    },    
    {
        label: '其他',
        options: [
            { value: '锁模力', label: '锁模力', desc: 'CLAMP' },
            { value: '可能堵嘴', label: '可能堵嘴', desc: 'NT' },
            // { value: '顶出力', label: '顶出力', desc: 'EFOR' },
            // { value: '开模速度', label: '开模速度', desc: 'OVEL' },
            // { value: '顶出速度', label: '顶出速度', desc: 'EVEL' },
        ]
    }
]
