export function getFullReportUrl(assertRelativeUrl:string) {
  if (!assertRelativeUrl) {
    return ''
  }
  else {
    return window.location.origin + '/storage/' + assertRelativeUrl
  }
}

export function getFullImageUrl(assertRelativeUrl:string) {
  if (!assertRelativeUrl) {
    return ''
  }
  else {
    return window.location.origin + '/storage/' + assertRelativeUrl
  }
}

export function getFullUrl(assertRelativeUrl:string) {
  if (!assertRelativeUrl) {
    return ''
  }
  else {
    return window.location.origin + '/storage/' + assertRelativeUrl
  }
}