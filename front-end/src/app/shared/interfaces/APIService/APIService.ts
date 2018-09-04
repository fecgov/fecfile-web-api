/**
 * Posts interface
 */
export interface Posts {
  body?: string,
  id?: number,
  title?: string,
  userid?: number
}

/**
 * Post interface
 */
 export interface Post {
  body?: string,
  id?: number,
  title?: string,
  userid?: number
 }

 export interface Auth {
   access_token?: string
 }
