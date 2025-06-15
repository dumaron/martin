# TODO

## Journal

### Create an entry about how using the computer to create daily suggestions does not trigger frustration
- [ ] Take pictures of the new computer-made daily suggestions
- [ ] Do a pomodoro to list base elements of the article

## Finances

### Pairing

- [ ] Fix CSS for main table: the `th` seems to be slightly higher than the `td`
- [ ] Show bank account as an element of the main table
- [ ] Create low-level pages (both list and detail) for bank imports
- [ ] Switch "memo" field in creation from a textarea to an input

#### Improve category selection by replacing native `select` with [TomSelect](https://github.com/orchidjs/tom-select)
- [ ] Try to change the category creation select by making it load with Tom Select

#### Improve "Analysis" tab
- [ ] Try changing the algorithm for similar transactions by removing some "too common" words and including some of the words at the end of the text
- [ ] Try developing a new version of the table that includes a new row below the main one with the potentially paired YNAB transaction
- [ ] Try adding a new column to the similar transactions which tells the percentage of different chars from the original text - after removing numbers and signs

#### Improve "Pairing" tabs
- [ ] Add a message for when there are no suggestions in pairing, both for exact match and similar date
- [ ] Add a column for the suggestions to show the difference in days from the bank transactions

#### Review "Nothing to pair page"
- [ ] Remove the quick actions for YNAB sync
- [ ] Add quick links to bank import or dashboard

#### Warnings for potentially duplicate bank transactions
- [ ] Chat with claude about how to create fixtures for integration tests on Django
- [ ] Try creating a test situation for that on local database and implement basic widget to show the warning

#### Implement mistakes
- [ ] Extend the bank transaction model with a boolean field to tell if it's a mistake
- [ ] Add a way to mark a bank transaction as a mistake during pairing in the "Other" tab
- [ ] When a bank transaction is marked as "mistake", add the red flag to the YNAB transaction if it exists
- [ ] When a bank transaction is paired to a YNAB trasnaction and is marked as "mistake", add the red flag to the YNAB transaction
 
### Dashboards
- [ ] Create a dashboard to show how many Bank transactions need to be paired
- [ ] On the dashboard above, list also all the YNAB transactions that are not paired and that are older than 2 months

## Productivity

### Daily suggestions

#### Have a basic printable version
- [ ] Create new models for daily suggestions, including just daily lists. The goal is to just do what I'm currently doing in "Pages"
- [ ] Add new menu voices for daily suggestions 
- [ ] Try creating basic flow page to fill daily suggestions for Today or Tomorrow
- [ ] Create a temporary page and try to print that

### Inboxes
- [ ] Create a flow page to review unreviewed notes
- [ ] Change "note" entity name to "inbox"
- [ ] Add basic low-level pages for inboxes

## General

### Improve menu
- [x] Rework menu to avoid "Finaces" section and to have "Flows", "Dashboards", "Low-level entities"
- [ ] Improve the "active" menu templatetag to support nested routes

### Improve tables
- [ ] Try a new version of tables' CSS, right now they're barely usable

## Motivation

### Daily memory
- [ ] Try to install the S3 image provider for Django
- [x] Setup an S3 account (went with Google Cloud storage)