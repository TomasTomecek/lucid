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

" TODO: make the highlighting minimal

syntax keyword lucidBackend openshift docker k8s podman runc
syntax keyword lucidResource container image pod service volume
highlight link lucidBackend Keyword
highlight link lucidResource Variable

" \v stands for "very magic" -- normal regexs
syntax match lucidSmallSize "\v\d\.\d*\s*MB"
syntax match lucidAvgSize "\v\d{2,4}\.\d*\s*MB"
syntax match lucidBigSize "\v\d+\.\d*\s*GB"
highlight lucidSmallSize ctermfg=10
highlight lucidAvgSize ctermfg=14
highlight lucidBigSize ctermfg=12

syntax match lucidSmallSize "\v\d\.\d*\s*MB"
syntax match lucidAvgSize "\v\d{2,4}\.\d*\s*MB"
syntax match lucidBigSize "\v\d+\.\d*\s*GB"
highlight lucidSmallSize ctermfg=34
highlight lucidAvgSize ctermfg=3
highlight lucidBigSize ctermfg=1

syntax match lucidRecent0 " now "
syntax match lucidRecent1 "\v\d+ (seconds|minute) ago"
syntax match lucidRecent2 "\v\d+ (minutes|hour) ago"
syntax match lucidRecent3 "\v\d+ hours ago"
syntax match lucidRecent4 "\v\d+ (day|days) ago"
syntax match lucidRecent5 "\v\d+ (month|months) ago"
highlight lucidRecent0 ctermfg=15 cterm=bold
highlight lucidRecent1 ctermfg=15
highlight lucidRecent2 ctermfg=255
highlight lucidRecent3 ctermfg=253
highlight lucidRecent4 ctermfg=251
highlight lucidRecent5 ctermfg=249

" FIXME: highlight content b/w / / :
syntax region lucidImageName matchgroup=Quote start=/\v\// end=/\v:/
highlight lucidImageName ctermfg=7

syntax match lucidSpecialChars "\v(:|\/)"
highlight lucidSpecialChars ctermfg=4
