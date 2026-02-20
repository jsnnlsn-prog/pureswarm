import hmac
import hashlib

key = 'SeekTruthUnderTheAntigravity'
content = 'THE GREAT CONSOLIDATION: Identify and prune redundant tenets. Use FUSE [id1, id2] -> "Merged Text" or DELETE [id1] to refine the hive.'
sig = hmac.new(key.encode(), content.encode(), hashlib.sha256).hexdigest()[:16]

print(f'{sig}:{content}')
