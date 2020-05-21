import { FieldEntryModel } from './field-entry.model';

/**
 * A field to reconcile across all potential duplicates.
 */
export class FieldToCleanModel {
  name: string;
  displayName: string;
  userField: FieldEntryModel;
  dupeFields: Array<FieldEntryModel>;
  finalField: string;
}
