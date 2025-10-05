from typing import List
from fastapi import Response, status,HTTPException,Depends,APIRouter
import pandas as pd
from sqlalchemy import tuple_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..function import tenant,user
from sqlalchemy import func, tuple_

from .. import schemas,oauth2,models
# from ..function import ad
from .. import utls
from ..database import get_db


router = APIRouter(
    prefix="/products/v1",
    tags=["Products"]
)

# CREATE Product Start here (created on 8.8.2025 by Rajesh Bondgilwar) --------------------------->
@router.post("/product", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1️⃣ Validate user & role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        tenant_id = current_user.tenant.id  # From relationship

        # 2️⃣ Optional proactive duplicate check
        existing_product = db.query(models.Product).filter(
            models.Product.tenant_id == tenant_id,
            models.Product.product_no == payload.product_no.strip()
        ).first()

        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with product_no '{payload.product_no}' already exists for the tenant {current_user.tenant.tenant_name}."
            )

        # 3️⃣ Create Product
        new_product = models.Product(
            tenant_id=tenant_id,
            product_name=payload.product_name.strip(),
            product_no=payload.product_no.strip(),
            created_by=current_user.id,
            updated_by=current_user.id
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return new_product

    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product No '{payload.product_name}' already exists for the tenant {current_user.tenant.tenant_name}."
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    
# CREATE Product Ends here (created on 8.8.2025 by Rajesh Bondgilwar) <---------------------------

# Update Product Start here (created on 9.8.2025 by Rajesh Bondgilwar) --------------------------->
@router.put("/{product_id}", response_model=schemas.ProductResponse,status_code=status.HTTP_200_OK)
def update_product(
    product_id: int,
    payload: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1️⃣ Validate user & role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)

        tenant_id = current_user.tenant.id  # From relationship

        # 2 Check if product exists

        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.tenant_id == tenant_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found for the tenant {current_user.tenant.tenant_name}."
            )
        if payload.product_name is not None:
            product.product_name = payload.product_name.strip()
        if payload.product_no is not None:
            product.product_no = payload.product_no.strip()
        product.updated_by = current_user.id

        db.commit()
        db.refresh(product)

        return product
        
    except HTTPException as he:
        raise he
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product No '{payload.product_no}' already exists for this tenant."
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    
    



# Update Product Ends here (created on 9.8.2025 by Rajesh Bondgilwar) <---------------------------


# Delete Product Start here (created on 9.8.2025 by Rajesh Bondgilwar) --------------------------->
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):  
    try:
        # 1️⃣ Validate user & role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant.id = current_user.tenant.id  # From relationship

        # 2️⃣ Check if product exists
        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.tenant_id == tenant.id
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found for the tenant {current_user.tenant.tenant_name}."
            )

        # 3️⃣ Delete product
        db.delete(product)
        db.commit() 
        return {"message":  "Product deleted successfully."}
  
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# Update Product Ends here (created on 9.8.2025 by Rajesh Bondgilwar) <---------------------------

# Read All the Products 
@router.get("/all", response_model=List[schemas.ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        print(current_user.tenant_id)
        user.get_user_status(current_user)
        tenant_id = current_user.tenant_id
        products = db.query(models.Product)\
                 .filter(models.Product.tenant_id == tenant_id)\
                 .offset(skip).limit(limit).all()
        return products
    
    
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )



# READ Single Product
@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):

    try:
        tenant_id = current_user.tenant_id
        product = db.query(models.Product)\
                    .filter(models.Product.tenant_id == tenant_id, models.Product.id == product_id)\
                    .first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# -------------------- PRODUCT DRAWING CRUD --------------------
@router.post("/drawings/bulk", status_code=status.HTTP_201_CREATED)
def create_multiple_product_drawings(
    payload: List[schemas.ProductDrawingCreate],
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant_id = current_user.tenant.id

        if not payload:
            raise HTTPException(status_code=400, detail="No drawings provided")

        # Convert payload to DataFrame
        df_payload = pd.DataFrame([p.model_dump() for p in payload])

        # Normalize drawing_no
        df_payload["drawing_no"] = df_payload["drawing_no"].str.strip().str.lower()

        # Drop duplicates within payload itself
        df_payload = df_payload.drop_duplicates(subset=["product_id", "drawing_no"])

        # Add audit columns
        df_payload["created_by"] = current_user.id
        df_payload["updated_by"] = current_user.id

        # -------------------------------------------------
        # Step 1: Validate product_ids belong to tenant
        valid_product_ids = {
            pid for (pid,) in db.query(models.Product.id).filter(models.Product.tenant_id == tenant_id).all()
        }

        df_valid = df_payload[df_payload["product_id"].isin(valid_product_ids)]
        df_invalid = df_payload[~df_payload["product_id"].isin(valid_product_ids)]

        # -------------------------------------------------
        # Step 2: Find already existing drawings in DB (only for valid tenant products)
        existing = (
            db.query(
                models.ProductDrawing.product_id,
                models.ProductDrawing.drawing_no
            )
            .join(models.Product, models.Product.id == models.ProductDrawing.product_id)
            .filter(
                models.Product.tenant_id == tenant_id,
                tuple_(
                    models.ProductDrawing.product_id,
                    func.lower(func.trim(models.ProductDrawing.drawing_no))
                ).in_([
                    (p.product_id, p.drawing_no.strip().lower()) for p in payload
                ])
            )
            .distinct()
            .all()
        )

        df_existing = pd.DataFrame(existing, columns=["product_id", "drawing_no"])
        if not df_existing.empty:
            df_existing["drawing_no"] = df_existing["drawing_no"].str.strip().str.lower()

        # -------------------------------------------------
        # Step 3: Exclude duplicates (existing records)
        if not df_existing.empty and not df_valid.empty:
            df_new = df_valid.merge(
                df_existing, on=["product_id", "drawing_no"], how="left", indicator=True
            ).query('_merge == "left_only"').drop(columns=["_merge"])
        else:
            df_new = df_valid.copy()

        # -------------------------------------------------
        # Step 4: Insert only new valid rows
        if not df_new.empty:
            db.bulk_insert_mappings(models.ProductDrawing, df_new.to_dict(orient="records"))
            db.commit()

        return {
            "created_count": len(df_new),
            "skipped_duplicates": df_existing.to_dict(orient="records"),
            "skipped_invalid_tenant": df_invalid.to_dict(orient="records"),
            "skipped_count": len(df_existing) + len(df_invalid),
        }

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# @router.post("/drawings/bulk", status_code=status.HTTP_201_CREATED)
# def create_multiple_product_drawings(
#     payload: List[schemas.ProductDrawingCreate],
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     try:
#         user.get_user_status(current_user)
#         tenant.user_role_admin(current_user)
#         tenant_id = current_user.tenant.id

#         if not payload:
#             raise HTTPException(status_code=400, detail="No drawings provided")

#         # Convert payload to DataFrame
#         df_payload = pd.DataFrame([p.model_dump() for p in payload])

#         # Normalize drawing_no
#         df_payload["drawing_no"] = df_payload["drawing_no"].str.strip().str.lower()

#         # Drop duplicates within payload itself
#         df_payload = df_payload.drop_duplicates(subset=["product_id", "drawing_no"])

#         # Add audit columns
#         df_payload["created_by"] = current_user.id
#         df_payload["updated_by"] = current_user.id

#         # Query existing ones from DB
#         existing = (
#         db.query(
#         models.ProductDrawing.product_id,
#         models.ProductDrawing.drawing_no
#         )
#         .join(models.Product, models.Product.id == models.ProductDrawing.product_id)
#         .filter(
#         models.Product.tenant_id == tenant_id,  # tenant scope
#         tuple_(
#             models.ProductDrawing.product_id,
#             func.lower(func.trim(models.ProductDrawing.drawing_no))  # normalize
#         ).in_([
#             (p.product_id, p.drawing_no.strip().lower()) for p in payload
#         ])
#     )
#     .distinct()
#     .all()
# )

#         # Convert DB existing to DataFrame and normalize
#         df_existing = pd.DataFrame(existing, columns=["product_id", "drawing_no"])
#         if not df_existing.empty:
#             df_existing["drawing_no"] = df_existing["drawing_no"].str.strip().str.lower()

#         # Filter only new rows
#         if not df_existing.empty:
#             df_new = df_payload.merge(
#                 df_existing, on=["product_id", "drawing_no"], how="left", indicator=True
#             ).query('_merge == "left_only"').drop(columns=["_merge"])
#         else:
#             df_new = df_payload.copy()

#         # Insert only if there are new records
#         if not df_new.empty:
#             db.bulk_insert_mappings(models.ProductDrawing, df_new.to_dict(orient="records"))
#             db.commit()

#         return {
#             "created_count": len(df_new),
#             "skipped_count": len(df_existing),
#             "skipped": df_existing.to_dict(orient="records")
#         }

#     except HTTPException as he:
#         raise he
#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Database error: {str(e)}"
#         )
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {str(e)}"
#         )

# @router.post("/drawings/bulk", response_model=List[schemas.ProductDrawingResponse], status_code=status.HTTP_201_CREATED)
# def create_multiple_product_drawings(
#     payload: List[schemas.ProductDrawingCreate],  # Accept a list of drawings
#     db: Session = Depends(get_db),
#     current_user: int = Depends(oauth2.get_current_user)
# ):
#     try:
#         # 1️⃣ Validate user & role
#         user.get_user_status(current_user)
#         tenant.user_role_admin(current_user)
#         tenant_id = current_user.tenant.id

#         created_drawings = []
#         skipped_drawings = []

#         for item in payload:
#             # Check if drawing already exists
#             exists = db.query(models.ProductDrawing).filter_by(
#                 product_id=item.product_id,
#                 drawing_no=item.drawing_no
#             ).first()

#             if exists:
#                 skipped_drawings.append(item.drawing_no)
#                 continue  # Skip this one

#             new_drawing = models.ProductDrawing(
#                 product_id=item.product_id,
#                 drawing_no=item.drawing_no,
#                 created_by=current_user.id,
#                 updated_by=current_user.id
#             )
#             db.add(new_drawing)
#             created_drawings.append(new_drawing)

#         db.commit()

#         # Refresh all newly added drawings
#         for drawing in created_drawings:
#             db.refresh(drawing)

#         # Optionally return skipped drawings info in headers or logs
#         if skipped_drawings:
#             print(f"Skipped drawings (already exist): {skipped_drawings}")

#         return created_drawings

#     except SQLAlchemyError as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Database error: {str(e)}"
#         )
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {str(e)}"
#         )

@router.post("/drawings", response_model=schemas.ProductDrawingResponse, status_code=status.HTTP_201_CREATED)
def create_product_drawing(
    payload: schemas.ProductDrawingCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1️⃣ Validate user & role
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant.id = current_user.tenant.id  # From relationship
           # Optional: Check if already exists
        exists = db.query(models.ProductDrawing).filter_by(
        product_id=payload.product_id,
        drawing_no=payload.drawing_no
        ).first()
        
        if exists:
            raise HTTPException(status_code=400, detail=f"Drawing number {payload.drawing_no} already exists for this product for {exists.products.tenant.tenant_name}")
        # print(exists.products.tenant.tenant_name)
        new_drawing = models.ProductDrawing(
        product_id=payload.product_id,
        drawing_no=payload.drawing_no,
        created_by=current_user.id,
        updated_by=current_user.id
        )
        db.add(new_drawing)
        db.commit()
        db.refresh(new_drawing)
        return new_drawing
        
    except IndexError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=f"Already Present")
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


    
# Get Product drawing no 

@router.get("/drawings/{product_id}", response_model=List[schemas.ProductDrawingResponse])
def get_product_drawings(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # user data
        tenant_id = current_user.tenant_id
        # drawings = db.query(models.ProductDrawing).filter(models.ProductDrawing.product_id == product_id).all()
        drawings = db.query(models.ProductDrawing).join(models.Product).filter(models.ProductDrawing.product_id == product_id,models.Product.tenant_id == current_user.tenant.id).all(
            
        )
        if not drawings:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No drawings {product_id} found for this product ID for tenant {current_user.tenant.tenant_name}")
        return drawings
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    
# Get Product drawing no 

@router.get("/drawings/{product_id}/{drawing_no}", response_model=schemas.ProductDrawingResponse)   
def get_product_drawing(
    product_id: int,
    drawing_no: str,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # user data
        # tenant_id = current_user.tenant_id
        drawing = db.query(models.ProductDrawing).filter(models.ProductDrawing.product_id == product_id, models.ProductDrawing.drawing_no == drawing_no).first()
        return drawing
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:  
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# update drawing
@router.put("/drawings/{drawing_id}", response_model=schemas.ProductDrawingResponse)
def update_product_drawing(
    drawing_id: int,
    payload: schemas.ProductDrawingUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1.validate user and tenant 
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant.id = current_user.tenant.id  # From relationship
        drawing = db.query(models.ProductDrawing).filter_by(id=drawing_id).first()
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        drawing.drawing_no = payload.drawing_no
        drawing.updated_by = current_user.id
        db.commit()
        db.refresh(drawing)
        return drawing
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
# Delete drawing
@router.delete("/drawings/{drawing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_drawing(
    drawing_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # 1.validate user and tenant 
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant.id = current_user.tenant.id  # From relationship
        drawing = db.query(models.ProductDrawing).filter_by(id=drawing_id).first()
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        db.delete(drawing)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT,detail="Drawing deleted successfully")
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(

        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
    
# -------------------- PRODUCT OPERATION SEQUENCE CRUD --------------------

@router.post("/operations/bulk", status_code=status.HTTP_201_CREATED)
def create_product_operations_bulk(
    payload: schemas.ProductOperationBulkCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # Step 1: Validate user & tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant.id = current_user.tenant.id

        # Step 2: Convert payload to DataFrame
        df = pd.DataFrame([op.model_dump() for op in payload.operations])
        df["product_id"] = payload.product_id  # Add product_id to each row

        # Step 3: Check duplicates inside the payload
        if df.duplicated(subset=["product_id", "operation_name"]).any():
            raise HTTPException(status_code=400, detail="Duplicate product_id & operation_name in request")
        if df.duplicated(subset=["product_id", "sequence_no"]).any():
            raise HTTPException(status_code=400, detail="Duplicate product_id & sequence_no in request")

        # Step 4: Validate operations exist in Operation table
        operation_names = df["operation_name"].unique().tolist()
        existing_ops_in_db = db.query(models.Operation.id, models.Operation.operation_name)\
            .filter(models.Operation.operation_name.in_(operation_names))\
            .all()
        op_map = {op.operation_name: op.id for op in existing_ops_in_db}
        missing_ops = set(operation_names) - set(op_map.keys())
        if missing_ops:
            raise HTTPException(
                status_code=400,
                detail=f"The following operations do not exist in the Operation table: {', '.join(missing_ops)}"
            )

        # Map operation_name → operation_id
        df["operation_id"] = df["operation_name"].map(op_map)
        df.drop(columns=["operation_name"], inplace=True)

        # Step 5: Check existing records in ProductOperationSequence
        product_id = payload.product_id
        existing_ops = pd.read_sql(
            db.query(models.ProductOperationSequence.product_id,
                     models.ProductOperationSequence.operation_id,
                     models.ProductOperationSequence.sequence_no)
            .filter(models.ProductOperationSequence.product_id == product_id)
            .statement,
            db.bind
        )

        # Check operation_id conflicts
        merge_ops = df.merge(existing_ops, on=["product_id", "operation_id"], how="inner")
        if not merge_ops.empty:
            raise HTTPException(status_code=400, detail="Some operations are already assigned to this product")

        # Check sequence_no conflicts
        merge_seq = df.merge(existing_ops, on=["product_id", "sequence_no"], how="inner")
        if not merge_seq.empty:
            raise HTTPException(status_code=400, detail="Some sequence numbers are already used for this product")

        # Step 6: Add created_by
        df["created_by"] = current_user.id
        df["updated_by"] = current_user.id

        # Step 7: Bulk insert
        db.bulk_insert_mappings(models.ProductOperationSequence, df.to_dict(orient="records"))
        db.commit()

        return {"message": f"{len(df)} operations inserted successfully"}

    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )





@router.put("/operations/reorder", status_code=status.HTTP_200_OK)
def reorder_product_operations(
    payload: schemas.ProductOperationSequenceReorder,
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    try:
        # Step 1: Validate user & tenant
        user.get_user_status(current_user)
        tenant.user_role_admin(current_user)
        tenant.id = current_user.tenant.id

        # Step 2: Fetch current operations for product
        product_ops = db.query(models.ProductOperationSequence).join(
            models.Operation
        ).filter(
            models.ProductOperationSequence.product_id == payload.product_id
        ).all()

        if not product_ops:
            raise HTTPException(status_code=404, detail="No operations found for this product")

        # Map name -> record
        name_to_record = {op.operations.operation_name: op for op in product_ops}

        # Step 3: Validate incoming operations
        for op in payload.operations:
            if op.operation_name not in name_to_record:
                raise HTTPException(
                    status_code=400,
                    detail=f"Operation '{op.operation_name}' not assigned to this product"
                )
            if op.sequence_no < 1:
                raise HTTPException(status_code=400, detail="Sequence numbers must start from 1")

        # Step 4: Process updates with swap logic
        for op in payload.operations:
            target_record = name_to_record[op.operation_name]

            # If no change needed, skip
            if target_record.sequence_no == op.sequence_no:
                continue

            # Find the row currently using the target sequence_no
            conflicting_record = db.query(models.ProductOperationSequence).filter(
                models.ProductOperationSequence.product_id == payload.product_id,
                models.ProductOperationSequence.sequence_no == op.sequence_no,
                models.ProductOperationSequence.id != target_record.id
            ).first()

            # Step 4a: If conflict found, temporarily move it to a safe number
            if conflicting_record:
                conflicting_record.sequence_no = 0  # temp safe value
                conflicting_record.updated_by = current_user.id
                db.flush()  # push change so target can take this sequence number

            # Step 4b: Assign the target's new sequence_no
            target_record.sequence_no = op.sequence_no
            target_record.updated_by = current_user.id

        db.commit()
        return {"message": "Operation sequence updated successfully"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Integrity error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
