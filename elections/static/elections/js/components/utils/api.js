export const formatedParamsToQueryStrings = (params) => {
  const initialParams = []
  // Convert object to arrays to be used by URLSearchParams
  if (params) {
    for (const param of Object.entries(params)) {
      if (!Array.isArray(param[1])) {
        initialParams.push([param[0], param[1]])
        continue
      }
      for (let i = 0; i < param[1].length; i++) {
        initialParams.push([param[0], param[1][i]])
      }
    }
  }
  let resultParams = ""
  if (initialParams.length > 0) {
    const queryParams = new URLSearchParams(initialParams)
    resultParams = "?" + queryParams
  }
   return resultParams
}


export const api = async (path, params) => {
  const resultParams = formatedParamsToQueryStrings(params)
  const url = `${path}${resultParams}`
  const response = await fetch(url.replace("%2B", "+"))
  const data = await response.json()
  return data
}
