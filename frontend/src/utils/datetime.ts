
var dateFormat = require('dateformat')

export function dateToday() {
  return dateFormat((new Date()), 'yyyy-mm-dd')
}

export function datetimeToday() {
  return dateFormat((new Date()), 'yyyy-mm-dd HH:MM:ss')
}
export function datetimeTodayStr() {
  return dateFormat((new Date()), 'yyyymmddHHMMss')
}
export function dateToDatetime(date: string){
  return dateFormat(date, 'yyyy-mm-dd HH:MM:ss')
}

export function datetimeToDate(datetime: string){
  return dateFormat(datetime, 'yyyy-mm-dd')
}

export function getDateTime(dateStr: string) {
  var st = dateStr; 
  var a = st.split(" "); 
  var b = a[0].split("-"); 
  var year = Number(b[0])
  var month = Number(b[1])
  var day = Number(b[2])
  var c = a[1].split(":"); 
  var hour = Number(c[0])
  var minute = Number(c[1])
  var second = Number(c[2])
  var date = new Date(year, month, day, hour, minute, second);
  return date; 
}

export function calDateTimeBetHours(befDate: string, aftDate: string) {

  var date1 = getDateTime(befDate) 
  var date2 = getDateTime(aftDate) 

  var s1 = date1.getTime()
  var s2 = date2.getTime()

  var total = (s2 - s1) / 1000
  var hours = total/(60*60)

  return hours
}
