# Identical bank transactions in one import

Open problem, found on 2026-11-22 while working on `bank-transaction-date-from-description`. Not addressed there.

## The problem

Bank transactions are unique on `(description, date, amount)`, and `BankFileImport.save()` relies on
`bulk_create(..., ignore_conflicts=True)` to skip rows already imported by a previous, overlapping export.

The constraint cannot tell apart two different things:

1. **The same row seen in two exports**: must be skipped.
2. **Two real transactions identical in every column, in the same export**: both must be kept.

In case 2 the second row is silently dropped, and the money is gone from Martin.

## The real case

Fineco export `movements_20261122.xlsx`, two bus tickets bought the same day:

| Data_Operazione | Data_Valuta | Uscite | Descrizione_Completa |
|---|---|---|---|
| 28/10/2026 | 26/10/2026 | -2 | TEP SPA WWW.TEP.PR.IT IT Carta N. ***** 013 Data operazione 26/10/26 |
| 28/10/2026 | 26/10/2026 | -2 | TEP SPA WWW.TEP.PR.IT IT Carta N. ***** 013 Data operazione 26/10/26 |

- 1 row out of 76 in that file.
- Fineco card descriptions have no time; Credem ones do (`-14/04/25-19:18`), so Credem is less exposed but not immune.
- The export has no transaction id and no running balance column, so nothing in the file tells the two rows apart
  besides appearing twice.
- It happened before the date change too: the two rows are equal on the booking date as well.
- How many were lost in the past cannot be found from the DB; only by re-reading the original files.

## Idea 1: an occurrence number

Add an `occurrence` column and put it in the unique constraint. While importing, number identical rows of the same
file in order (1, 2, ...). A later export containing both rows again numbers them the same way and skips both.

- Works for every bank.
- Existing rows all become occurrence 1: the migration changes nothing.
- Re-importing old files would recover the lost rows as occurrence 2 without duplicating anything else.
- Assumes identical transactions always land in the same export. If an export window cut that day in half, the
  second ticket would arrive later as occurrence 1 and be taken for the first one. Overlapping exports by a few days
  makes this unlikely, not impossible.

## Idea 2: count instead of constrain

Drop the unique constraint. For each `(description, date, amount)` key, count the rows in the file and in the DB,
and insert only the difference.

- Same outcome as idea 1, no new column.
- Loses the database guarantee against duplicates; the import logic gets more complex.

## Open question: how this meets `duplicate_of`

`duplicate_of` links a transaction to an already paired one when the bank changes the description between two
exports (`get_potential_duplicate`: same amount and date, different description, already paired).

With identical twins this gets harder. If both TEP tickets change description in the next export:

- both new rows match both old rows on amount and date, so `get_potential_duplicate` cannot know that new #1 is
  old #1 and new #2 is old #2;
- with idea 1, the occurrence number of the new rows is computed on the new description, so it says nothing about
  which old row each one replaces;
- for twins it probably does not matter which old row each new row links to, as they are interchangeable, but the
  count must match: two new rows must link to two different old rows, not both to the first.

To figure out before choosing an approach:

- whether linking twins "in any order, one each" is acceptable;
- whether `get_potential_duplicate` should exclude old rows already used as `duplicate_of` target;
- whether the "alias" model mentioned in the `BankTransaction.duplicate_of` comment (one transaction, many
  descriptions) would solve both problems at once.
