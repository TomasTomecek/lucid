function! VisualSelection()
    if mode()=="v"
        let [line_start, column_start] = getpos("v")[1:2]
        let [line_end, column_end] = getpos(".")[1:2]
    else
        let [line_start, column_start] = getpos("'<")[1:2]
        let [line_end, column_end] = getpos("'>")[1:2]
    end
    return [line_start, column_start, line_end, column_end]
endfunction

function! LucidInitMapping()
    "TODO: there is 2nd deletion executed for a selection
    "08:38:04.473 __init__.py       DEBUG  delete(args = [[1, 1, 1, 2147483647]])
    vnoremap <buffer> d :call _cui_delete(VisualSelection())<CR>'
    nnoremap <buffer> dd :silent call _cui_delete()<CR>'
    nnoremap <buffer> <CR> :silent call LucidShowDetails(getpos("."))<CR>'
endfunction

nnoremap <silent> <Leader>l :call LucidRun()<CR>
