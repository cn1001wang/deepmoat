import type { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request: AxiosInstance = axios.create({
  baseURL: 'http://localhost:5005',
  timeout: 60000,
  // headers: { 'Content-Type': ContentTypeEnum.JSON },
})
async function requestHandler(config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> {
  return config
}

export interface ResponseBody<T = any> {
  code: number
  data: T
  msg: string
}
function responseHandler(response: any): ResponseBody<any> | AxiosResponse<any> | Promise<any> | any {
  const resData = response.data
  // 如果是Blob格式直接返回
  if (resData instanceof Blob)
    return resData

  if (resData.code === 200) {
    return resData
  }
  else {
    ElMessage.error(resData.msg)
    return Promise.reject(new Error(resData.msg))
  }
}
function errorHandler(error: AxiosError): Promise<any> {
  console.log('HTTP ERROR:', error)

  const { data, statusText } = error.response as AxiosResponse<ResponseBody>
  ElMessage.error(data?.msg || statusText)

  return Promise.reject(error)
}
request.interceptors.request.use(requestHandler)

request.interceptors.response.use(responseHandler, errorHandler)

export default request
