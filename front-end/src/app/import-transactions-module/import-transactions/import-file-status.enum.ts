/**
 * Enumeration of status values used in the workflow when importing a transaction file.
 */
export enum ImportFileStatusEnum {
  queued = 'Queued',
  uploading = 'Uploading',
  review = 'Review',
  failed = 'Failed',
  clean = 'Clean',
  importing = 'Importing',
  complete = 'Complete'
}
