from fastmcp import FastMCP
import pandas as pd
import json
from io import StringIO
from typing import Optional
import os

mcp = FastMCP("CSV Data Cleaning Server")

def load_csv(csv_path: str) -> pd.DataFrame:
    """Load CSV from file path or string content."""
    print(f"Attempting to read CSV from: {csv_path}")
    
    # First, try to detect if this is a file path or CSV content
    # More robust detection: if it contains commas and newlines, it might be CSV content
    if '\n' in csv_path and ',' in csv_path[:csv_path.find('\n')]:  # Check if first line has commas
        # Likely CSV content as string
        try:
            df = pd.read_csv(StringIO(csv_path))
            print(f"Successfully loaded CSV from string content with {len(df)} rows")
            return df
        except:
            # If string parsing fails, it might be a file path after all
            pass
    
    # Assume it's a file path
    try:
        # Convert to absolute path to handle different working directories
        if not os.path.isabs(csv_path):
            # Try current directory first
            full_path = os.path.abspath(csv_path)
            if os.path.exists(full_path):
                df = pd.read_csv(full_path)
                print(f"Successfully loaded CSV from: {full_path}")
                return df
            else:
                # Try common locations
                for base_dir in ['.', './data', '../data', './datasets']:
                    try_path = os.path.join(base_dir, csv_path)
                    if os.path.exists(try_path):
                        df = pd.read_csv(try_path)
                        print(f"Successfully loaded CSV from: {try_path}")
                        return df
                # If not found in common locations, try original path anyway
                df = pd.read_csv(csv_path)
                print(f"Successfully loaded CSV from: {csv_path}")
                return df
        else:
            # It's already an absolute path
            df = pd.read_csv(csv_path)
            print(f"Successfully loaded CSV from: {csv_path}")
            return df
        
    except Exception as e:
        # If file path fails, try as CSV string content
        try:
            df = pd.read_csv(StringIO(csv_path))
            print(f"Successfully loaded CSV from string content")
            return df
        except:
            raise Exception(f"Failed to read CSV from path '{csv_path}' or as string content: {str(e)}")

@mcp.tool
def inspect_csv(csv_path: str) -> str:
    """
    Inspect a CSV file to show basic information, missing values, and data types.
    
    Args:
        csv_path: Path to the CSV file or CSV string content
    
    Returns:
        JSON string with file information
    """
    try:
        df = load_csv(csv_path)
        
        info = {
            "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
            "missing_percentages": {col: float(round(df[col].isna().sum() / len(df) * 100, 2)) for col in df.columns},
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB",
            "sample_data": df.head(3).to_dict('records'),
            "file_path_used": str(csv_path)  # Add this for debugging
        }
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error inspecting CSV: {str(e)}"

@mcp.tool
def remove_null_rows(csv_path: str, columns: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Remove rows with null values from CSV.
    
    Args:
        csv_path: Path to the CSV file
        columns: Comma-separated column names to check for nulls (optional, checks all if not provided)
        output_path: Path to save cleaned CSV (optional, returns preview if not provided)
    
    Returns:
        Success message with statistics or preview of cleaned data
    """
    try:
        df = load_csv(csv_path)
        original_rows = len(df)
        
        if columns:
            col_list = [col.strip() for col in columns.split(',')]
            df_cleaned = df.dropna(subset=col_list)
        else:
            df_cleaned = df.dropna()
        
        removed_rows = original_rows - len(df_cleaned)
        
        if output_path:
            df_cleaned.to_csv(output_path, index=False)
            return f"Removed {removed_rows} rows with null values. Saved to {output_path}. Remaining rows: {len(df_cleaned)}"
        else:
            preview = df_cleaned.head(5).to_string()
            return f"Removed {removed_rows} rows. Remaining: {len(df_cleaned)} rows\n\nPreview:\n{preview}"
    except Exception as e:
        return f"Error removing null rows: {str(e)}"

@mcp.tool
def fill_missing_values(csv_path: str, strategy: str, columns: Optional[str] = None, 
                        fill_value: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Fill missing values in CSV using various strategies.
    
    Args:
        csv_path: Path to the CSV file
        strategy: Strategy to use - 'mean', 'median', 'mode', 'forward', 'backward', 'constant'
        columns: Comma-separated column names to fill (optional, fills all numeric/applicable columns if not provided)
        fill_value: Value to use when strategy is 'constant'
        output_path: Path to save cleaned CSV (optional)
    
    Returns:
        Success message with statistics
    """
    try:
        df = load_csv(csv_path)
        df_filled = df.copy()
        
        col_list = [col.strip() for col in columns.split(',')] if columns else df.columns.tolist()
        
        for col in col_list:
            if col not in df.columns:
                continue
                
            missing_count = df[col].isna().sum()
            if missing_count == 0:
                continue
            
            if strategy == 'mean':
                if pd.api.types.is_numeric_dtype(df[col]):
                    df_filled[col] = df[col].fillna(df[col].mean())
            elif strategy == 'median':
                if pd.api.types.is_numeric_dtype(df[col]):
                    df_filled[col] = df[col].fillna(df[col].median())
            elif strategy == 'mode':
                mode_val = df[col].mode()
                if not mode_val.empty:
                    df_filled[col] = df[col].fillna(mode_val[0])
            elif strategy == 'forward':
                df_filled[col] = df[col].ffill()
            elif strategy == 'backward':
                df_filled[col] = df[col].bfill()
            elif strategy == 'constant':
                if fill_value is None:
                    return "Error: fill_value required when strategy is 'constant'"
                df_filled[col] = df[col].fillna(fill_value)
            else:
                return f"Error: Unknown strategy '{strategy}'"
        
        if output_path:
            df_filled.to_csv(output_path, index=False)
            return f"Filled missing values using '{strategy}' strategy. Saved to {output_path}"
        else:
            preview = df_filled.head(5).to_string()
            return f"Filled missing values using '{strategy}' strategy\n\nPreview:\n{preview}"
    except Exception as e:
        return f"Error filling missing values: {str(e)}"

@mcp.tool
def remove_duplicates(csv_path: str, columns: Optional[str] = None, keep: str = 'first',
                        output_path: Optional[str] = None) -> str:
    """
    Remove duplicate rows from CSV.
    
    Args:
        csv_path: Path to the CSV file
        columns: Comma-separated column names to check for duplicates (optional, checks all if not provided)
        keep: Which duplicate to keep - 'first', 'last', or 'none' (removes all duplicates)
        output_path: Path to save cleaned CSV (optional)
    
    Returns:
        Success message with count of removed duplicates
    """
    try:
        df = load_csv(csv_path)
        original_rows = len(df)
        
        col_list = [col.strip() for col in columns.split(',')] if columns else None
        keep_value = False if keep == 'none' else keep
        
        df_cleaned = df.drop_duplicates(subset=col_list, keep=keep_value)
        removed = original_rows - len(df_cleaned)
        
        if output_path:
            df_cleaned.to_csv(output_path, index=False)
            return f"Removed {removed} duplicate rows. Saved to {output_path}. Remaining rows: {len(df_cleaned)}"
        else:
            preview = df_cleaned.head(5).to_string()
            return f"Removed {removed} duplicate rows. Remaining: {len(df_cleaned)} rows\n\nPreview:\n{preview}"
    except Exception as e:
        return f"Error removing duplicates: {str(e)}"

@mcp.tool
def standardize_columns(csv_path: str, operation: str, columns: Optional[str] = None,
                        output_path: Optional[str] = None) -> str:
    """
    Standardize column values (lowercase, uppercase, trim, title case).
    
    Args:
        csv_path: Path to the CSV file
        operation: Operation to perform - 'lower', 'upper', 'trim', 'title'
        columns: Comma-separated column names (optional, applies to all string columns if not provided)
        output_path: Path to save cleaned CSV (optional)
    
    Returns:
        Success message
    """
    try:
        df = load_csv(csv_path)
        
        col_list = [col.strip() for col in columns.split(',')] if columns else df.select_dtypes(include=['object']).columns.tolist()
        
        for col in col_list:
            if col not in df.columns:
                continue
            
            if operation == 'lower':
                df[col] = df[col].astype(str).str.lower()
            elif operation == 'upper':
                df[col] = df[col].astype(str).str.upper()
            elif operation == 'trim':
                df[col] = df[col].astype(str).str.strip()
            elif operation == 'title':
                df[col] = df[col].astype(str).str.title()
            else:
                return f"Error: Unknown operation '{operation}'"
        
        if output_path:
            df.to_csv(output_path, index=False)
            return f"Applied '{operation}' to columns: {', '.join(col_list)}. Saved to {output_path}"
        else:
            preview = df.head(5).to_string()
            return f"Applied '{operation}' to columns: {', '.join(col_list)}\n\nPreview:\n{preview}"
    except Exception as e:
        return f"Error standardizing columns: {str(e)}"

@mcp.tool
def filter_rows(csv_path: str, column: str, operator: str, value: str,
                output_path: Optional[str] = None) -> str:
    """
    Filter rows based on condition.
    
    Args:
        csv_path: Path to the CSV file
        column: Column name to filter on
        operator: Operator - 'equals', 'not_equals', 'greater', 'less', 'contains', 'not_contains'
        value: Value to compare against
        output_path: Path to save filtered CSV (optional)
    
    Returns:
        Success message with filtered row count
    """
    try:
        df = load_csv(csv_path)
        
        if column not in df.columns:
            return f"Error: Column '{column}' not found in CSV. Available columns: {list(df.columns)}"
        
        if operator == 'equals':
            df_filtered = df[df[column] == value]
        elif operator == 'not_equals':
            df_filtered = df[df[column] != value]
        elif operator == 'greater':
            df_filtered = df[pd.to_numeric(df[column], errors='coerce') > float(value)]
        elif operator == 'less':
            df_filtered = df[pd.to_numeric(df[column], errors='coerce') < float(value)]
        elif operator == 'contains':
            df_filtered = df[df[column].astype(str).str.contains(value, na=False)]
        elif operator == 'not_contains':
            df_filtered = df[~df[column].astype(str).str.contains(value, na=False)]
        else:
            return f"Error: Unknown operator '{operator}'. Valid operators: equals, not_equals, greater, less, contains, not_contains"
        
        if output_path:
            df_filtered.to_csv(output_path, index=False)
            return f"Filtered to {len(df_filtered)} rows (from {len(df)}). Saved to {output_path}"
        else:
            preview = df_filtered.head(5).to_string()
            return f"Filtered to {len(df_filtered)} rows (from {len(df)})\n\nPreview:\n{preview}"
    except Exception as e:
        return f"Error filtering rows: {str(e)}"



if __name__ == "__main__":
    print("Starting MCP server for CSV Data Cleaning")
    print("Current working directory:", os.getcwd())
    print("Available files in current directory:", os.listdir('.'))
    mcp.run()