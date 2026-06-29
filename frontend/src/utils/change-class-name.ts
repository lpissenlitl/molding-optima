// Check if an element has a class
export const hasClass = (ele: HTMLElement, className: string) => {
    return !!ele.className.match(new RegExp('(\\s|^)' + className + '(\\s|$)'))
  }
  
  // Add class to element
  export const addClass = (ele: HTMLElement, className: string) => {
    if (!hasClass(ele, className)) ele.className += ' ' + className
  }
  
  // Remove class from element
  export const removeClass = (ele: HTMLElement, className: string) => {
    if (hasClass(ele, className)) {
      const reg = new RegExp('(\\s|^)' + className + '(\\s|$)')
      ele.className = ele.className.replace(reg, ' ')
    }
  }
  
  // Toggle class for the selected element
  export const toggleClass = (ele: HTMLElement, className: string) => {
    if (!ele || !className) {
      return
    }
    let classString = ele.className
    const nameIndex = classString.indexOf(className)
    if (nameIndex === -1) {
      classString += '' + className
    } else {
      classString =
        classString.substr(0, nameIndex) +
        classString.substr(nameIndex + className.length)
    }
    ele.className = classString
  }