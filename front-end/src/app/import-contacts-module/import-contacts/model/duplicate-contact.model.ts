import { ImportContactModel } from './import-contact.model';

export class DuplicateContactModel extends ImportContactModel {

  potentialDupes: Array<DuplicateContactModel>;
  seq: number;

  constructor(duplicate: any) {
    super(duplicate);
    this.potentialDupes = duplicate.potentialDupes ? duplicate.potentialDupes : [];
    this.seq = duplicate.seq ? duplicate.seq : null;
  }
}
