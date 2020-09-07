# A python library for executing S42 files to format addresses

Example usage:

```python
import s42.template

template = s42.template.Template.from_file_path('...')

dto = {
  'U40.13.00.00': 'LL20 8RZ', 
  'U40.14.00.00': 'Great Britain',
  'U40.16.00.00': 'LLANGOLLEN',
  'U40.21.11.41': 'Llangollen',
  'U40.21.21.41': 'Heol Esgob',
  'U40.24.00.00': '2',
  'U50.50.00.00': 'Latn',
  'U50.51.00.00': 'en',
  'U50.53.00.00': 'GB',
  'U50.54.00.00': 'GB'
}

print(template.render(dto))
```

Which outputs:

```text
2 Heol Esgob
Llangollen
LLANGOLLEN
LL20 8RZ
```