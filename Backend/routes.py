# # backend/routes.py
# from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
# from pydantic import BaseModel
# from datetime import datetime
# import json
# from .db import conn
# from .utils import upload_to_web3_storage, recompute_score, call_asi_chat
# from .embeddings import create_embeddings_and_store, retrieve_relevant_texts

# router = APIRouter()

# class ChatRequest(BaseModel):
#     user_id: str | None
#     message: str

# @router.post("/create_inft")
# async def create_inft(name: str = Form(...), owner: str = Form(...), cid: str = Form(...), tag: str = Form(...),
#                       file: UploadFile = File(...), traits: str = Form("{}"), description: str = Form("")):
#     content = await file.read()
#     # cid = upload_to_web3_storage(content, file.filename)

#     cur = conn.cursor()
#     cur.execute("INSERT INTO infts (name, owner, tag, cid, traits_json, description, nfid, created_at) VALUES (?,?,?,?,?,?,?,?)",
#                 (name, owner, tag, cid, traits, description, inft_id, datetime.utcnow().isoformat()))
#     inft_id = cur.lastrowid
#     conn.commit()

#     text_chunks = []
#     try:
#         text = content.decode("utf-8")
#         for part in text.split("\n\n"):
#             if len(part.strip()) > 20:
#                 text_chunks.append(part.strip())
#     except:
#         try:
#             trait_text = json.loads(traits)
#             text_chunks = trait_text if isinstance(trait_text, list) else [str(trait_text)]
#         except:
#             text_chunks = []

#     if text_chunks:
#         create_embeddings_and_store(inft_id, text_chunks)

#     return {"inft_id": inft_id, "cid": cid}
# # @router.post("/create_inft")
# # async def create_inft(
# #     name: str = Body(...),
# #     owner: str = Body(...),
# #     tag: str = Body(...),
# #     cid: str = Body(...),
# #     traits: str = Body("{}")
# # ):
# #     cur = conn.cursor()
# #     print("Creating iNFT with:", name, owner, tag, cid, traits)
# #     cur.execute(
# #         "INSERT INTO infts (name, owner, tag, cid, traits_json, created_at) VALUES (?,?,?,?,?,?)",
# #         (name, owner, tag, cid, traits, datetime.utcnow().isoformat())
# #     )
# #     inft_id = cur.lastrowid
# #     conn.commit()

# #     # Try to extract text chunks for embeddings
# #     text_chunks = []
# #     try:
# #         trait_text = json.loads(traits)
# #         if isinstance(trait_text, list):
# #             text_chunks = [json.dumps(t) for t in trait_text]
# #         else:
# #             text_chunks = [str(trait_text)]
# #     except:
# #         text_chunks = []

# #     if text_chunks:
# #         create_embeddings_and_store(inft_id, text_chunks)

# #     return {"inft_id": inft_id, "cid": cid}



# # @app.post("/create_inft", response_model=CreateINFTResponse)
# # async def create_inft(
# #     name: str = Form(...),
# #     owner: str = Form(...),
# #     tag: str = Form(...),
# #     traits: str = Form("[]")  # JSON string (list of {key,value})
# # ):
# #     # --- normalize traits ---
# #     try:
# #         raw_traits = json.loads(traits) if traits else []
# #     except Exception:
# #         raw_traits = []

# #     normalized = []
# #     if isinstance(raw_traits, dict):
# #         # { "color": "blue" } → [ {"key":"color","value":"blue"} ]
# #         normalized = [{"key": k, "value": str(v)} for k, v in raw_traits.items()]
# #     elif isinstance(raw_traits, list):
# #         for t in raw_traits:
# #             if isinstance(t, dict) and "key" in t and "value" in t:
# #                 normalized.append({"key": str(t["key"]), "value": str(t["value"])})
# #             else:
# #                 # fallback for string values
# #                 normalized.append({"key": str(t), "value": ""})
# #     else:
# #         normalized = []

# #     traits_json = json.dumps(normalized)

# #     # mock a CID (since no file)
# #     cid = f"mockCID-{name}-{int(time.time())}"

# #     # store in DB
# #     cur = conn.cursor()
# #     cur.execute(
# #         "INSERT INTO infts (name, owner, tag, cid, traits_json, created_at) VALUES (?,?,?,?,?,?)",
# #         (name, owner, tag, cid, traits_json, datetime.utcnow().isoformat())
# #     )
# #     inft_id = cur.lastrowid
# #     conn.commit()

# #     # embeddings based only on traits
# #     if normalized:
# #         text_chunks = [f"{t['key']}={t['value']}" for t in normalized]
# #         create_embeddings_and_store(inft_id, text_chunks)

# #     return {"inft_id": inft_id, "cid": cid}


# @router.get("/list_infts")
# def list_infts():
#     cur = conn.cursor()
#     cur.execute("SELECT id, name, owner, tag, cid, traits_json, score, created_at FROM infts ORDER BY id DESC")
#     rows = cur.fetchall()
#     return [
#         {"id": r[0], "name": r[1], "owner": r[2], "tag": r[3], "cid": r[4],
#          "traits": json.loads(r[5]) if r[5] else [], "score": r[6], "created_at": r[7]}
#         for r in rows
#     ]

# @router.post("/chat/{inft_id}")
# async def chat_with_inft(inft_id: int, req: ChatRequest):
#     cur = conn.cursor()
#     cur.execute("SELECT name, owner, tag, traits_json FROM infts WHERE id=?", (inft_id,))
#     row = cur.fetchone()
#     if not row:
#         raise HTTPException(status_code=404, detail="iNFT not found")
#     name, owner, tag, traits_json = row
#     traits = json.loads(traits_json) if traits_json else []

#     retrieved = retrieve_relevant_texts(inft_id, req.message, k=3)
#     persona = f"Persona: name={name}, tag={tag}, traits={traits}"
#     if retrieved:
#         persona += "\nRelevant memory:\n" + "\n---\n".join(retrieved)

#     reply = call_asi_chat(system_prompt=persona, user_message=req.message)
#     return {"reply": reply}

# @router.post("/feedback/{inft_id}")
# async def submit_feedback(inft_id: int, rating: float = Form(...), comment: str = Form("")):
#     if rating < 0 or rating > 10:
#         raise HTTPException(status_code=400, detail="rating must be 0..10")
#     cur = conn.cursor()
#     cur.execute("INSERT INTO feedbacks (inft_id, rating, comment, created_at) VALUES (?,?,?,?)",
#                 (inft_id, rating, comment, datetime.utcnow().isoformat()))
#     conn.commit()
#     new_score = recompute_score(inft_id)
#     return {"new_score": new_score}
# backend/routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime
import json
from .db import conn
from .utils import upload_to_web3_storage, recompute_score, call_asi_chat
from .embeddings import create_embeddings_and_store, retrieve_relevant_texts

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str | None
    message: str

@router.post("/create_inft")
async def create_inft(
    name: str = Form(...), 
    owner: str = Form(...), 
    cid: str = Form(...), 
    tag: str = Form(...),
    file: UploadFile = File(...), 
    traits: str = Form("{}"), 
    description: str = Form(""),
    nft_id: str = Form(None)  # Accept NFT ID from frontend
):
    content = await file.read()
    # cid = upload_to_web3_storage(content, file.filename)

    cur = conn.cursor()
    # Insert into database with the provided nft_id stored as nfid
    cur.execute(
        "INSERT INTO infts (name, owner, tag, cid, traits_json, description, nfid, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (name, owner, tag, cid, traits, description, nft_id, datetime.utcnow().isoformat())
    )
    inft_id = cur.lastrowid  # This is the auto-increment primary key
    conn.commit()

    # Process text chunks for embeddings
    text_chunks = []
    try:
        # First try to decode file content
        text = content.decode("utf-8")
        for part in text.split("\n\n"):
            if len(part.strip()) > 20:
                text_chunks.append(part.strip())
    except:
        # If file content fails, use traits for embeddings
        try:
            trait_data = json.loads(traits)
            if isinstance(trait_data, list):
                # Convert trait objects to readable text
                for trait in trait_data:
                    if isinstance(trait, dict) and 'key' in trait and 'value' in trait:
                        text_chunks.append(f"{trait['key']}: {trait['value']}")
            else:
                text_chunks = [str(trait_data)]
        except:
            text_chunks = []
    
    # Add name and description to embeddings for better context
    if name:
        text_chunks.append(f"Name: {name}")
    if description:
        text_chunks.append(f"Description: {description}")

    if text_chunks:
        create_embeddings_and_store(inft_id, text_chunks)

    return {"inft_id": inft_id, "cid": cid, "nft_id": nft_id}

@router.get("/list_infts")
def list_infts():
    cur = conn.cursor()
    cur.execute("SELECT id, name, owner, tag, cid, traits_json, score, nfid, created_at FROM infts ORDER BY id DESC")
    rows = cur.fetchall()
    return [
        {
            "id": r[0], 
            "name": r[1], 
            "owner": r[2], 
            "tag": r[3], 
            "cid": r[4],
            "traits": json.loads(r[5]) if r[5] else [], 
            "score": r[6], 
            "nft_id": r[7],  # Include NFT ID in response
            "created_at": r[8]
        }
        for r in rows
    ]

@router.post("/chat/{inft_id}")
async def chat_with_inft(inft_id: int, req: ChatRequest):
    cur = conn.cursor()
    # Get iNFT data including the nft_id (nfid)
    cur.execute("SELECT name, owner, tag, traits_json, nfid FROM infts WHERE id=?", (inft_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="iNFT not found")
    
    name, owner, tag, traits_json, nft_id = row
    traits = json.loads(traits_json) if traits_json else []

    # Retrieve relevant context from embeddings
    retrieved = retrieve_relevant_texts(inft_id, req.message, k=3)
    
    # Build persona with NFT information
    persona = f"Persona: name={name}, tag={tag}, traits={traits}"
    if nft_id:
        persona += f", nft_id={nft_id}"
    if retrieved:
        persona += "\nRelevant memory:\n" + "\n---\n".join(retrieved)

    # Generate AI response
    reply = call_asi_chat(system_prompt=persona, user_message=req.message)
    return {"reply": reply, "nft_id": nft_id}

@router.post("/feedback/{inft_id}")
async def submit_feedback(inft_id: int, rating: float = Form(...), comment: str = Form("")):
    if rating < 0 or rating > 10:
        raise HTTPException(status_code=400, detail="rating must be 0..10")
    cur = conn.cursor()
    cur.execute("INSERT INTO feedbacks (inft_id, rating, comment, created_at) VALUES (?,?,?,?)",
                (inft_id, rating, comment, datetime.utcnow().isoformat()))
    conn.commit()
    new_score = recompute_score(inft_id)
    return {"new_score": new_score}

# Optional: Get iNFT by NFT ID instead of internal ID
@router.get("/inft/by_nft_id/{nft_id}")
def get_inft_by_nft_id(nft_id: str):
    cur = conn.cursor()
    cur.execute("SELECT id, name, owner, tag, cid, traits_json, score, nfid, created_at FROM infts WHERE nfid=?", (nft_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="iNFT not found")
    
    return {
        "id": row[0],
        "name": row[1],
        "owner": row[2],
        "tag": row[3],
        "cid": row[4],
        "traits": json.loads(row[5]) if row[5] else [],
        "score": row[6],
        "nft_id": row[7],
        "created_at": row[8]
    }

# Optional: Chat with iNFT by NFT ID
@router.post("/chat/by_nft_id/{nft_id}")
async def chat_with_inft_by_nft_id(nft_id: str, req: ChatRequest):
    cur = conn.cursor()
    # First get the internal ID from the NFT ID
    cur.execute("SELECT id FROM infts WHERE nfid=?", (nft_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="iNFT not found")
    
    internal_id = row[0]
    # Use the existing chat function
    return await chat_with_inft(internal_id, req)